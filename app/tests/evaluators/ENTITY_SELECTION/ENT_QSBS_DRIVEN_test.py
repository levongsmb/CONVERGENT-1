"""Tests for ENT_QSBS_DRIVEN evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.ENTITY_SELECTION.ENT_QSBS_DRIVEN import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_passthrough(rules):
    """QSBS founder fixture: already C corp, no pass-through → not_applicable."""
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_not_applicable_with_short_horizon_no_liquidity(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["planning"]["time_horizon_years"] = 2
    base["planning"]["liquidity_event_planned"] = None

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False
    assert "3y" in result.reason


def test_applicable_on_scorp_owner_with_long_horizon(rules):
    """MFJ S corp owner fixture has 10y horizon → applicable."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["horizon_years"] == 10
    assert Decimal(trace["post_obbba_cap_usd"]) == Decimal("15000000")
    # Max savings = 15M × 23.8% = 3,570,000
    assert Decimal(trace["max_per_taxpayer_savings_full_exclusion"]) == Decimal("3570000.00")


def test_applicable_on_partnership_owner_long_horizon(rules):
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True


def test_applicable_with_liquidity_event_even_short_horizon(rules):
    """Liquidity fixture has 20y horizon AND planned event 18 months out.
    Applicable because of both the horizon and the liquidity event."""
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert result.computation_trace["liquidity_event_planned"] is True


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "QSBS_ORIGINAL_ISSUANCE" in result.cross_strategy_impacts
    assert "QSBS_HOLDING_PERIOD" in result.cross_strategy_impacts
    assert "QSBS_STACKING" in result.cross_strategy_impacts
    assert "CA_NONCONFORMITY_QSBS" in result.cross_strategy_impacts


def test_pin_cites_include_1202_and_351(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§1202(a)" in c for c in result.pin_cites)
    assert any("(b)(4)" in c for c in result.pin_cites)
    assert any("§351" in c for c in result.pin_cites)
    assert any("§70431" in c for c in result.pin_cites)
