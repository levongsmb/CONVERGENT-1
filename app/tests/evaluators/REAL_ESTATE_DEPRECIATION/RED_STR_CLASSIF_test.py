"""Tests for RED_STR_CLASSIF evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.REAL_ESTATE_DEPRECIATION.RED_STR_CLASSIF import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_rental(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_real_estate_investor_fixture(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["candidate_rental_asset_count"] >= 1
    assert Decimal(trace["current_rental_loss"]) == Decimal("42000")


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "LL_469_PASSIVE" in result.cross_strategy_impacts
    assert "LL_REP_STATUS" in result.cross_strategy_impacts
    assert "RED_COST_SEG" in result.cross_strategy_impacts
    assert "NIIT_REP_PLANNING" in result.cross_strategy_impacts


def test_pin_cites_include_reg_469_1T(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§1.469-1T(e)(3)(ii)(A)" in c for c in result.pin_cites)
    assert any("§1.469-1T(e)(3)(ii)(B)" in c for c in result.pin_cites)
    assert any("Bailey" in c for c in result.pin_cites)


def test_implementation_steps_cover_7_and_30_day_rules(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    steps = " ".join(result.implementation_steps)
    assert "7 days" in steps or "≤ 7" in steps
    assert "30 days" in steps or "≤ 30" in steps


def test_inputs_required_covers_material_participation_docs(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    inputs = " ".join(result.inputs_required)
    assert "material-participation" in inputs
    assert "§1.469-5T" in inputs
