"""Tests for SALE_ASSET_VS_STOCK evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.SALE_TRANSACTION.SALE_ASSET_VS_STOCK import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_liquidity_event(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_liquidity_event_fixture(rules):
    """Liquidity fixture: S corp target, stock basis $1.85M, proceeds $18M.
    Gross gain = $16.15M.
    S corp asset sale: 30% ordinary × 37% + 70% capital × 23.8%
      = $16.15M × (0.30 × 0.37 + 0.70 × 0.238)
      = $16.15M × (0.111 + 0.1666) = $16.15M × 0.2776 = $4,483,240
    S corp stock sale: $16.15M × 23.8% = $3,843,700
    Swing = $639,540 (asset more expensive).
    """
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["gross_gain"]) == Decimal("16150000.00")
    assert trace["narrative"] == "S_CORP_338_RECAPTURE_EXPOSURE"
    asset_total = Decimal(trace["asset_sale_total_tax"])
    stock_total = Decimal(trace["stock_sale_total_tax"])
    swing = asset_total - stock_total
    assert Decimal(trace["swing_asset_minus_stock"]) == swing.quantize(Decimal("0.01"))


def test_not_applicable_without_expected_proceeds(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_liquidity_event.yaml").read_text()
    )
    del base["planning"]["liquidity_event_planned"]["expected_proceeds"]

    from app.scenario.models import ClientScenario

    # Model-level validator flags missing expected_proceeds; evaluator guards
    # before reaching the pydantic check. Use a minimal override to reach
    # the evaluator's guard directly.
    # Restore validation requirement via workaround: add back with None,
    # but ClientScenario schema treats Dict without strict structure.
    base["planning"]["liquidity_event_planned"]["expected_proceeds"] = None

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_c_corp_narrative(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_qsbs_founder.yaml").read_text()
    )
    # QSBS founder scenario already has a C corp target with liquidity event
    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["narrative"] == "C_CORP_DOUBLE_TAX_ON_ASSET_SALE"


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "SALE_F_REORG" in result.cross_strategy_impacts
    assert "SALE_BASIS_CLEANUP" in result.cross_strategy_impacts
    assert "SALE_338H10" in result.cross_strategy_impacts
    assert "INST_STANDARD_453" in result.cross_strategy_impacts


def test_pin_cites_include_338h10_and_1060(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§338(h)(10)" in c for c in result.pin_cites)
    assert any("§1060" in c for c in result.pin_cites)
    assert any("§336(e)" in c for c in result.pin_cites)
    assert any("Rev. Rul. 2008-18" in c for c in result.pin_cites)
