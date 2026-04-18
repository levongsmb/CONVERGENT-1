"""Tests for CGL_TAX_LOSS_HARVEST evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.CAPITAL_GAINS_LOSSES.CGL_TAX_LOSS_HARVEST import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_taxable_securities(rules):
    """MFJ S corp owner fixture has only a residence (not a taxable security)."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_not_applicable_when_no_unrealized_losses(rules):
    """Single fixture has RSU_LOT_2025 at $18,400 basis, $24,900 FMV → gain, no loss."""
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_when_unrealized_loss_exists(rules):
    """Liquidity-event fixture has INVEST_PORTFOLIO_LT (basis $1.4M, FMV $2.15M)
    = unrealized gain not loss. Construct a scenario with an unrealized loss."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_liquidity_event.yaml").read_text()
    )
    # Swap FMV and basis so portfolio shows a loss
    for a in base["assets"]:
        if a["asset_code"] == "INVEST_PORTFOLIO_LT":
            a["cost_basis"] = 2000000
            a["adjusted_basis"] = 2000000
            a["fmv"] = 1700000  # $300K unrealized loss

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["total_unrealized_loss"]) == Decimal("300000")
    # LT offset against $34,000 realized LT gain:
    #   offset_against_lt = min(300000, 34000) = 34000
    #   saving_on_lt = 34000 * 0.238 = 8,092
    # Ordinary offset = $3,000 cap * 0.32 = $960
    # Headline = 8092 + 960 = 9,052
    assert Decimal(trace["offset_against_lt"]) == Decimal("34000")
    assert result.estimated_tax_savings == Decimal("9052.00")


def test_deferred_loss_banked_to_carryforward(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_liquidity_event.yaml").read_text()
    )
    for a in base["assets"]:
        if a["asset_code"] == "INVEST_PORTFOLIO_LT":
            a["cost_basis"] = 2000000
            a["adjusted_basis"] = 2000000
            a["fmv"] = 1700000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    # Deferred = 300000 - 34000 (LT offset) - 3000 (ordinary) = 263000
    assert Decimal(trace["deferred_loss_to_carryforward"]) == Decimal("263000")


def test_cross_strategy_impacts(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_liquidity_event.yaml").read_text()
    )
    for a in base["assets"]:
        if a["asset_code"] == "INVEST_PORTFOLIO_LT":
            a["cost_basis"] = 2000000
            a["adjusted_basis"] = 2000000
            a["fmv"] = 1700000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "CGL_WASH_SALES" in result.cross_strategy_impacts
    assert "CGL_CARRYFORWARDS" in result.cross_strategy_impacts
    assert "NIIT_CAP_GAIN_HARVEST" in result.cross_strategy_impacts


def test_pin_cites_include_1091_and_1211(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_liquidity_event.yaml").read_text()
    )
    for a in base["assets"]:
        if a["asset_code"] == "INVEST_PORTFOLIO_LT":
            a["cost_basis"] = 2000000
            a["adjusted_basis"] = 2000000
            a["fmv"] = 1700000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§1091" in c for c in result.pin_cites)
    assert any("§1211" in c for c in result.pin_cites)
    assert any("§1212" in c for c in result.pin_cites)
    assert any("§1.1012-1" in c for c in result.pin_cites)
