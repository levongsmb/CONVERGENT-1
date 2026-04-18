"""Tests for LL_469_PASSIVE evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.LOSS_LIMIT_NAVIGATION.LL_469_PASSIVE import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_suspended_or_rental(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_real_estate_investor_fixture(rules):
    """Real estate fixture has $118,400 suspended + $42,000 current rental loss."""
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["prior_suspended_passive_losses"]) == Decimal("118400")
    assert Decimal(trace["current_rental_loss"]) == Decimal("42000")
    assert Decimal(trace["aggregate_passive_losses_awaiting_release"]) == Decimal("160400")


def test_current_rental_loss_only_triggers_applicability(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["income"]["rental_income_net"] = -15000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert Decimal(result.computation_trace["current_rental_loss"]) == Decimal("15000")


def test_cross_strategy_impacts_listed(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "LL_REP_STATUS" in result.cross_strategy_impacts
    assert "LL_STR_EXCEPTION" in result.cross_strategy_impacts
    assert "LL_DISPOSITION_FREE_SL" in result.cross_strategy_impacts


def test_pin_cites_include_469_and_safe_harbor(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§469" in c for c in result.pin_cites)
    assert any("Rev. Proc. 2019-38" in c for c in result.pin_cites)
    assert any("§469(g)" in c for c in result.pin_cites)
