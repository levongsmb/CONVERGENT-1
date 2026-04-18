"""Tests for CAP_FIRST_TIME_ABATE."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_FIRST_TIME_ABATE import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_applicable(rules):
    assert Evaluator().evaluate(_load("scenario_single_1040"), rules, 2026).applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(_load("scenario_single_1040"), rules, 2026)
    assert "CAP_PENALTY_ABATEMENT" in r.cross_strategy_impacts
    assert "CAP_REASONABLE_CAUSE" in r.cross_strategy_impacts


def test_pin_cites(rules):
    r = Evaluator().evaluate(_load("scenario_single_1040"), rules, 2026)
    assert any("IRM 20.1.1.3.6.1" in c for c in r.pin_cites)
    assert any("Rev. Proc. 2019-46" in c for c in r.pin_cites)


def test_implementation_steps(rules):
    r = Evaluator().evaluate(_load("scenario_single_1040"), rules, 2026)
    steps = " ".join(r.implementation_steps)
    assert "FTA" in steps
    assert "Form 843" in steps


def test_not_applicable_branch_absent_by_design(rules):
    # FTA availability does not short-circuit; evaluator surfaces the option
    # on every scenario. Confirm this is intentional.
    r = Evaluator().evaluate(_load("scenario_liquidity_event"), rules, 2026)
    assert r.applicable is True
