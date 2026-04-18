"""Tests for CAP_7508A_DISASTER."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_7508A_DISASTER import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert "CA_DISASTER_LOSS" in r.cross_strategy_impacts
    assert "CAP_PENALTY_ABATEMENT" in r.cross_strategy_impacts


def test_pin_cites_include_7508A_and_165i(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("§7508A" in c for c in r.pin_cites)
    assert any("§165(i)" in c for c in r.pin_cites)
    assert any("§1033" in c for c in r.pin_cites)


def test_risks_warn_about_fed_declaration_requirement(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "federally declared" in risks.lower()


def test_implementation_covers_election_paths(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    steps = " ".join(r.implementation_steps)
    assert "§165(i)" in steps
    assert "§1033" in steps
