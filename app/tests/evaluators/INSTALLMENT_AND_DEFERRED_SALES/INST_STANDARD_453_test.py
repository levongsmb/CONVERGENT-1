"""Tests for INST_STANDARD_453 evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.INSTALLMENT_AND_DEFERRED_SALES.INST_STANDARD_453 import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_liquidity_event(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_liquidity_event_with_earnout(rules):
    """Liquidity fixture has earnout_component_pct = 15, expected_proceeds $18M.
    Deferred principal = $18M × 15% = $2.7M (below $5M threshold).
    Gross gain $16.15M; deferred gain = $16.15M × 15% = $2,422,500.
    Deferred tax at 23.8% = $576,555.
    PV over 5 years at 7%: 1/1.07 + 1/1.07^2 + ... / 5 factor
    """
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["deferred_principal"]) == Decimal("2700000.00")
    assert Decimal(trace["deferred_gain"]) == Decimal("2422500.00")
    assert trace["exceeds_453a_5m_threshold"] is False
    assert Decimal(trace["npv_benefit"]) > Decimal(0)


def test_not_applicable_when_no_earnout_component(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_liquidity_event.yaml").read_text()
    )
    base["planning"]["liquidity_event_planned"]["earnout_component_pct"] = 0

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_453a_threshold_flagged_above_5m(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_liquidity_event.yaml").read_text()
    )
    # Boost earnout to 50% → deferred principal $9M > $5M threshold
    base["planning"]["liquidity_event_planned"]["earnout_component_pct"] = 50

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert trace["exceeds_453a_5m_threshold"] is True
    assert Decimal(trace["a_453_interest_proxy"]) > Decimal(0)


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "SALE_EARNOUTS" in result.cross_strategy_impacts
    assert "INST_RECAPTURE_ACCEL" in result.cross_strategy_impacts
    assert "CA_INSTALLMENT_SOURCING" in result.cross_strategy_impacts
    assert "NIIT_INSTALL_TIMING" in result.cross_strategy_impacts


def test_pin_cites_include_453a_and_453i(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§453A" in c for c in result.pin_cites)
    assert any("§453(i)" in c for c in result.pin_cites)
    assert any("§453(e)" in c for c in result.pin_cites)
    assert any("§453A(d)" in c for c in result.pin_cites)
