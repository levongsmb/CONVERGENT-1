"""Tests for CR_RND_41 evaluator."""

from __future__ import annotations

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.CREDITS.CR_RND_41 import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_operating_entity(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_scorp_owner_classified_on_regular_track(rules):
    """MFJ S corp owner fixture: gross receipts $1.61M prior year → startup track (under $5M)."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    startup = trace["startup_track_entities"]
    assert len(startup) == 1
    assert startup[0]["entity_code"] == "SCORP_PRIMARY"


def test_liquidity_target_on_regular_track(rules):
    """Liquidity fixture: $6.45M gross prior year → regular track (above $5M)."""
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    regular = trace["regular_track_entities"]
    assert len(regular) == 1
    assert regular[0]["entity_code"] == "SCORP_TARGET"


def test_qsbs_founder_c_corp_on_regular_track(rules):
    """QSBS founder fixture C corp: gross $7.2M prior year → regular track."""
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    regular = trace["regular_track_entities"]
    assert len(regular) == 1
    assert regular[0]["entity_code"] == "CCORP_FOUNDER"


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "AM_174A_DOMESTIC_RE" in result.cross_strategy_impacts
    assert "RND_280C_COORD" in result.cross_strategy_impacts
    assert "CR_STARTUP_PAYROLL_OFFSET" in result.cross_strategy_impacts
    assert "CR_ORDERING_LIMITS" in result.cross_strategy_impacts


def test_pin_cites_include_41a_41h_280c(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§41(a)" in c for c in result.pin_cites)
    assert any("§41(h)" in c for c in result.pin_cites)
    assert any("§41(c)(4)" in c for c in result.pin_cites)
    assert any("§280C" in c for c in result.pin_cites)
    assert any("§1.41-4" in c for c in result.pin_cites)
