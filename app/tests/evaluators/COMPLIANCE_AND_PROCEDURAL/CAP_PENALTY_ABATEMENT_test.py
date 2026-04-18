"""Tests for CAP_PENALTY_ABATEMENT evaluator."""

from __future__ import annotations

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_PENALTY_ABATEMENT import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_applicable_on_any_scenario(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "CAP_FIRST_TIME_ABATE" in result.cross_strategy_impacts
    assert "CAP_REASONABLE_CAUSE" in result.cross_strategy_impacts
    assert "CAP_EXAMS_APPEALS" in result.cross_strategy_impacts


def test_pin_cites_include_6651_and_irm(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§6651" in c for c in result.pin_cites)
    assert any("IRM 20.1.1.3" in c for c in result.pin_cites)
    assert any("Rev. Proc. 2019-46" in c for c in result.pin_cites)


def test_implementation_steps_cover_fta_and_reasonable_cause(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    steps = " ".join(result.implementation_steps)
    assert "transcript" in steps.lower()
    assert "Form 843" in steps
    assert "20.1.1.3" in steps


def test_not_applicable_only_returns_false_when_gated(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    # This evaluator has no gating — always applicable
    assert result.applicable is True
