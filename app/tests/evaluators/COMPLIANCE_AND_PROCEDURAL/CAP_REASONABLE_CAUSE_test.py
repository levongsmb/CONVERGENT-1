"""Tests for CAP_REASONABLE_CAUSE."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_REASONABLE_CAUSE import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert "CAP_FIRST_TIME_ABATE" in r.cross_strategy_impacts
    assert "CAP_EXAMS_APPEALS" in r.cross_strategy_impacts


def test_pin_cites_include_boyle(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("Boyle" in c for c in r.pin_cites)
    assert any("§6651(a)" in c for c in r.pin_cites)
    assert any("§6664(c)" in c for c in r.pin_cites)


def test_implementation_steps_reference_irm(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    steps = " ".join(r.implementation_steps)
    assert "IRM 20.1.1.3.2" in steps


def test_risks_cite_boyle_limitation(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "Boyle" in risks
