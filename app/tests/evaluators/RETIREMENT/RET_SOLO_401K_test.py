"""Tests for RET_SOLO_401K evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.RETIREMENT.RET_SOLO_401K import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_wage_only_taxpayer(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_single_owner_scorp_fixture(rules):
    """MFJ S corp owner fixture with 100% ownership, age ~46 (DOB 1980-03-22) → no catch-up."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["catchup_tier"] == "NONE"
    # W-2 wages = $195,000; employer PS = 25% = $48,750
    assert Decimal(trace["earnings_base"]) == Decimal("195000.00")
    assert Decimal(trace["employer_ps"]) == Decimal("48750.00")
    # Employee deferral $24,500 + employer PS $48,750 = $73,250
    # But §415(c) cap is $72,000; so max = $72,000
    assert Decimal(trace["max_total_before_catchup"]) == Decimal("72000")


def test_catchup_tier_age_50(rules):
    """Liquidity-event fixture primary DOB 1968 → age 58 in 2026 → AGE_50 tier."""
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["catchup_tier"] == "AGE_50"
    assert Decimal(trace["applicable_catchup"]) == Decimal("8000")


def test_super_catchup_60_63_detected(rules):
    """Construct a scenario with primary DOB 1965 → age 61 in 2026."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["identity"]["primary_dob"] = "1965-05-15"

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["catchup_tier"] == "SUPER_CATCHUP_60_63"
    assert Decimal(trace["applicable_catchup"]) == Decimal("11250")


def test_cross_strategy_impacts_listed(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "COMP_WAGE_DIST_SPLIT" in result.cross_strategy_impacts
    assert "RET_CASH_BALANCE" in result.cross_strategy_impacts
    assert "RET_CTRL_GROUP" in result.cross_strategy_impacts


def test_pin_cites_include_402g_415c_and_secure2(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§402(g)" in c for c in result.pin_cites)
    assert any("§415(c)" in c for c in result.pin_cites)
    assert any("SECURE 2.0" in c for c in result.pin_cites)
    assert any("Notice 2025-67" in c for c in result.pin_cites)


def test_reads_retirement_limits_from_config(rules):
    calls = []

    class Spy:
        def __init__(self, w):
            self.w = w

        def get(self, k, y):
            calls.append((k, y))
            return self.w.get(k, y)

        @property
        def version(self):
            return self.w.version

    scenario = _load("scenario_mfj_scorp_owner")
    Evaluator().evaluate(scenario, Spy(rules), year=2026)
    assert ("federal/retirement_limits", 2026) in calls
