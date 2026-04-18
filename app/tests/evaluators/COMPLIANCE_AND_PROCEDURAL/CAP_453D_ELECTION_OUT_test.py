"""Tests for CAP_453D_ELECTION_OUT."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_453D_ELECTION_OUT import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert "INST_STANDARD_453" in r.cross_strategy_impacts
    assert "INST_ELECTION_OUT" in r.cross_strategy_impacts
    assert "CGL_CARRYFORWARDS" in r.cross_strategy_impacts


def test_pin_cites_include_453d(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("§453(d)" in c for c in r.pin_cites)
    assert any("§15A.453-1" in c for c in r.pin_cites)


def test_risks_warn_irrevocable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "IRREVOCABLE" in risks or "irrevocable" in risks


def test_assumptions_all_or_nothing(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    a = " ".join(r.assumptions)
    assert "all-or-nothing" in a.lower()
