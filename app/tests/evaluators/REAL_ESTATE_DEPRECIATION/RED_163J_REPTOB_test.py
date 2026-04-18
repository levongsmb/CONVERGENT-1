"""Tests for RED_163J_REPTOB evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.REAL_ESTATE_DEPRECIATION.RED_163J_REPTOB import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_real_property_or_rental_entity(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_real_estate_investor_fixture(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["has_real_property"] is True
    assert trace["has_rental_entity"] is True
    assert trace["election_irrevocable"] is True


def test_carryover_surfaced_in_trace(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_real_estate_investor.yaml").read_text()
    )
    base["prior_year"]["suspended_163j_carryover"] = 85000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert Decimal(result.computation_trace["prior_163j_carryover"]) == Decimal("85000")


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "LL_163J_INTEREST" in result.cross_strategy_impacts
    assert "RED_COST_SEG" in result.cross_strategy_impacts
    assert "RED_BONUS_DEPR" in result.cross_strategy_impacts
    assert "RED_ADS_VS_GDS" in result.cross_strategy_impacts


def test_pin_cites_include_163j7b_and_168g(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§163(j)(7)(B)" in c for c in result.pin_cites)
    assert any("§168(g)" in c for c in result.pin_cites)
    assert any("IRREVOCABLE" in a.upper() or "irrevocable" in a for a in result.assumptions)


def test_implementation_steps_mention_reg(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    steps = " ".join(result.implementation_steps)
    assert "§1.163(j)-9(e)" in steps
    assert "ADS" in steps
