"""Tests for RET_ROTH_CONVERSION evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.RETIREMENT.RET_ROTH_CONVERSION import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_young_taxpayer_no_distributions(rules):
    """Single fixture: age 35 in 2026, no distributions → not_applicable."""
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_for_50plus_taxpayer(rules):
    """Liquidity-event fixture: primary DOB 1968 → age 58 → PRE_RETIREMENT window."""
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert result.computation_trace["window"] == "PRE_RETIREMENT"


def test_super_window_for_age_60_to_72(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["identity"]["primary_dob"] = "1963-03-15"  # age 63 in 2026

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert result.computation_trace["window"] == "SUPER_WINDOW"


def test_post_rmd_window(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["identity"]["primary_dob"] = "1950-01-01"  # age 76

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert result.computation_trace["window"] == "POST_RMD"


def test_senior_headroom_when_age_65plus_and_below_threshold(rules):
    """Age 67 MFJ with MAGI $100K: senior phaseout threshold $150K → headroom $50K."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["identity"]["primary_dob"] = "1959-01-01"  # age 67
    base["income"]["wages_primary"] = 60000
    base["income"]["wages_spouse"] = 40000
    base["income"]["interest_ordinary"] = 0
    base["income"]["dividends_qualified"] = 0
    base["income"]["capital_gains_long_term"] = 0
    base["income"]["k1_income"] = []

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert Decimal(trace["senior_headroom"]) == Decimal("50000")


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "RET_OBBBA_SENIOR_DEDUCTION" in result.cross_strategy_impacts
    assert "NIIT_ROTH_INTERACT" in result.cross_strategy_impacts
    assert "RD_CA_DOMICILE_BREAK" in result.cross_strategy_impacts


def test_pin_cites_include_roth_mechanics(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§408A(d)(3)" in c for c in result.pin_cites)
    assert any("§151(f)" in c for c in result.pin_cites)
    assert any("five-year" in c for c in result.pin_cites)
