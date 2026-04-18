"""Tests for CAP_8275_DISCLOSURE."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_8275_DISCLOSURE import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert "CAP_REASONABLE_CAUSE" in r.cross_strategy_impacts
    assert "CAP_EXAMS_APPEALS" in r.cross_strategy_impacts


def test_pin_cites_include_6662_and_6694(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("§6662(d)" in c for c in r.pin_cites)
    assert any("§6694" in c for c in r.pin_cites)
    assert any("Rev. Proc. 2023-14" in c for c in r.pin_cites)


def test_assumptions_distinguish_8275_and_8275R(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    a = " ".join(r.assumptions)
    assert "8275-R" in a
    assert "8275" in a


def test_risks_warn_about_tax_shelters(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "shelter" in risks.lower() or "tax-shelter" in risks.lower()
