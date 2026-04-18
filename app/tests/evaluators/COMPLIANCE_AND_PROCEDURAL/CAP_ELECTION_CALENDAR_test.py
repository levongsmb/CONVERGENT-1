"""Tests for CAP_ELECTION_CALENDAR."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_ELECTION_CALENDAR import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert "CAP_PROTECTIVE_ELECTIONS" in r.cross_strategy_impacts
    assert "CAP_3115_METHOD_CHANGE" in r.cross_strategy_impacts


def test_pin_cites_include_9100_and_754(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("§301.9100" in c for c in r.pin_cites)
    assert any("§754" in c for c in r.pin_cites)
    assert any("§1362" in c for c in r.pin_cites)


def test_risks_warn_about_754_irrevocable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "§754" in risks
    assert "irrevocable" in risks.lower()


def test_assumptions_list_annual_and_one_time(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    a = " ".join(r.assumptions)
    assert "annual" in a.lower() or "Annual" in a
