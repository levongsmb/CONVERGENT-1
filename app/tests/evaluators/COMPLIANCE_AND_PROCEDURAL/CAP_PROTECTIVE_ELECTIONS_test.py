"""Tests for CAP_PROTECTIVE_ELECTIONS."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_PROTECTIVE_ELECTIONS import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert "CAP_STATUTE_MGMT" in r.cross_strategy_impacts
    assert "CAP_ELECTION_CALENDAR" in r.cross_strategy_impacts


def test_pin_cites_include_6511(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("§6511" in c for c in r.pin_cites)
    assert any("9100" in c for c in r.pin_cites)


def test_implementation_steps_cover_9100(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    steps = " ".join(r.implementation_steps)
    assert "§301.9100-3" in steps or "§9100" in steps
    assert "Form 843" in steps or "Form 1040-X" in steps


def test_assumptions_cover_contingent_event(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assumptions = " ".join(r.assumptions)
    assert "contingent" in assumptions.lower()


def test_pin_cites_include_6511_b_2(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("IRC §6511(b)(2)" in c for c in r.pin_cites)


def test_cap_vs_deadline_distinction_surfaced(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    combined = " ".join(r.assumptions) + " " + " ".join(r.risks_and_caveats)
    assert "§6511(a)" in combined and "§6511(b)(2)" in combined
    assert "filing" in combined.lower() or "deadline" in combined.lower()
    assert "lookback" in combined.lower() or "cap" in combined.lower()


def test_lookback_cap_qualitatively_surfaced_when_deadline_met(rules):
    # Scenario premise: §6511(a) filing deadline is met, but the §6511(b)(2)
    # lookback would cap recovery. Schema does not carry payment history,
    # so the limitation must surface qualitatively in risks_and_caveats.
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "§6511(b)(2)" in risks
    assert "lookback" in risks.lower() or "cap" in risks.lower()
    assert "$0" in risks or "recover" in risks.lower()
