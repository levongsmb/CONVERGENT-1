"""Tests for CAP_IDENTITY_POA."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_IDENTITY_POA import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert "CAP_EXAMS_APPEALS" in r.cross_strategy_impacts
    assert "CAP_STATUTE_MGMT" in r.cross_strategy_impacts


def test_pin_cites_include_2848_and_14039(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("Form 2848" in c for c in r.pin_cites)
    assert any("Form 14039" in c for c in r.pin_cites)
    assert any("Form 8821" in c for c in r.pin_cites)


def test_assumptions_distinguish_2848_and_8821(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    a = " ".join(r.assumptions)
    assert "2848" in a
    assert "8821" in a


def test_implementation_caf(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    steps = " ".join(r.implementation_steps)
    assert "CAF" in steps
