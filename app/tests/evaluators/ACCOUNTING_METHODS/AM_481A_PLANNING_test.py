"""Tests for AM_481A_PLANNING evaluator."""

from __future__ import annotations

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.ACCOUNTING_METHODS.AM_481A_PLANNING import Evaluator
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


def test_applicable_on_scorp_owner_fixture(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert result.computation_trace["candidate_entity_count"] == 1


def test_applicable_on_partnership_owner_fixture(rules):
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "AM_CASH_VS_ACCRUAL" in result.cross_strategy_impacts
    assert "AM_174A_DOMESTIC_RE" in result.cross_strategy_impacts
    assert "RED_COST_SEG" in result.cross_strategy_impacts
    assert "CAP_3115_METHOD_CHANGE" in result.cross_strategy_impacts


def test_pin_cites_include_481a_and_rev_procs(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§481(a)" in c for c in result.pin_cites)
    assert any("§446(e)" in c for c in result.pin_cites)
    assert any("Rev. Proc. 2015-13" in c for c in result.pin_cites)
    assert any("Rev. Proc. 2023-24" in c for c in result.pin_cites)


def test_assumptions_cover_positive_and_negative_spread(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    text = " ".join(result.assumptions)
    assert "Positive" in text or "positive" in text
    assert "4 years" in text or "4-year" in text
    assert "Negative" in text or "negative" in text
