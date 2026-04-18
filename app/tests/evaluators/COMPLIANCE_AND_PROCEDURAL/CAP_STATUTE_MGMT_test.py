"""Tests for CAP_STATUTE_MGMT."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_STATUTE_MGMT import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy_includes_international(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert "IO_FBAR_FATCA" in r.cross_strategy_impacts
    assert "IO_5471_5472" in r.cross_strategy_impacts


def test_pin_cites_include_6501_and_irm(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("§6501(a)" in c or "§6501 " in c for c in r.pin_cites)
    assert any("§6501(c)(8)" in c for c in r.pin_cites)
    assert any("IRM 25.6.22" in c for c in r.pin_cites)


def test_assumptions_cover_fraud_and_foreign(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    a = " ".join(r.assumptions)
    assert "fraud" in a.lower()
    assert "foreign" in a.lower()


def test_risks_warn_about_form_872(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "Form 872" in risks
