"""Tests for LL_REP_STATUS evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.LOSS_LIMIT_NAVIGATION.LL_REP_STATUS import Evaluator
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
    assert Decimal(trace["current_rental_loss"]) == Decimal("42000")
    assert Decimal(trace["suspended_passive_losses"]) == Decimal("118400")
    assert Decimal(trace["potential_release_if_qualified"]) == Decimal("160400")


def test_cross_strategy_impacts_listed(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "LL_469_PASSIVE" in result.cross_strategy_impacts
    assert "LL_469_GROUPING" in result.cross_strategy_impacts
    assert "NIIT_REP_PLANNING" in result.cross_strategy_impacts


def test_pin_cites_include_469c7_and_reg(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§469(c)(7)" in c for c in result.pin_cites)
    assert any("§1.469-9" in c for c in result.pin_cites)
    assert any("750-hour" in c for c in result.pin_cites)


def test_implementation_steps_cover_aggregation_and_material_participation(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    steps = " ".join(result.implementation_steps)
    assert "§1.469-9(g)" in steps
    assert "§1.469-5T" in steps
    assert "750" in steps


def test_inputs_required_enumerate_substantiation(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    inputs_text = " ".join(result.inputs_required)
    assert "contemporaneous" in inputs_text
    assert "50%" in inputs_text
