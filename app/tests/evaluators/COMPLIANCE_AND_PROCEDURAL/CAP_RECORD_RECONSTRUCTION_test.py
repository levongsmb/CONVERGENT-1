"""Tests for CAP_RECORD_RECONSTRUCTION."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_RECORD_RECONSTRUCTION import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert "CAP_7508A_DISASTER" in r.cross_strategy_impacts
    assert "CAP_EXAMS_APPEALS" in r.cross_strategy_impacts


def test_pin_cites_include_cohan_and_274d(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("Cohan" in c for c in r.pin_cites)
    assert any("§274(d)" in c for c in r.pin_cites)
    assert any("§6001" in c for c in r.pin_cites)


def test_risks_warn_about_274d_strict_substantiation(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "§274(d)" in risks


def test_implementation_steps_cover_third_party_sources(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    steps = " ".join(r.implementation_steps)
    assert "bank" in steps.lower() or "vendor" in steps.lower()
