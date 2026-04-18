"""Tests for RET_BACKDOOR_ROTH evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.RETIREMENT.RET_BACKDOOR_ROTH import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_when_magi_below_phaseout_mfj(rules):
    """Construct an MFJ scenario with MAGI below $242K."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["income"]["wages_primary"] = 100000
    base["income"]["wages_spouse"] = 50000
    base["income"]["interest_ordinary"] = 0
    base["income"]["dividends_qualified"] = 0
    base["income"]["capital_gains_long_term"] = 0
    # Zero out K-1 as well
    base["income"]["k1_income"] = []

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False
    assert "below" in result.reason
    assert "Roth" in result.reason


def test_applicable_for_high_magi_mfj(rules):
    """MFJ S corp owner fixture has MAGI ~$947K, far above $252K phaseout high."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["filing_status"] == "MFJ"
    assert Decimal(trace["phaseout_low"]) == Decimal("242000")
    assert Decimal(trace["phaseout_high"]) == Decimal("252000")
    # IRA limit for age 46 primary = $7,500 (no catch-up)
    assert Decimal(trace["annual_ira_contribution_limit"]) == Decimal("7500")


def test_applicable_for_single_high_income(rules):
    """QSBS founder fixture: SINGLE with wages $240K + other income -> MAGI well above $153K phaseout low."""
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["filing_status"] == "SINGLE_OR_HOH"


def test_age_50_catchup_included(rules):
    """Liquidity-event fixture: primary DOB 1968 → age 58 in 2026.
    IRA contribution = $7,500 + $1,100 catch-up = $8,600."""
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["annual_ira_contribution_limit"]) == Decimal("8600")


def test_cross_strategy_impacts_listed(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "RET_SOLO_401K" in result.cross_strategy_impacts
    assert "RET_MEGA_BACKDOOR_ROTH" in result.cross_strategy_impacts
    assert "RET_ROTH_CONVERSION" in result.cross_strategy_impacts


def test_pin_cites_include_roth_mechanics(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§219" in c for c in result.pin_cites)
    assert any("§408(d)(2)" in c for c in result.pin_cites)
    assert any("§408A(c)(3)" in c for c in result.pin_cites)
    assert any("§408A(d)(3)" in c for c in result.pin_cites)


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
