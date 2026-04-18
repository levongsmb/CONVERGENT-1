"""Tests for CAP_ACCOUNTING_METHOD_DEFENSE."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_ACCOUNTING_METHOD_DEFENSE import Evaluator
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
    assert "CAP_3115_METHOD_CHANGE" in r.cross_strategy_impacts
    assert "AM_481A_PLANNING" in r.cross_strategy_impacts


def test_pin_cites_include_446b(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("§446(b)" in c for c in r.pin_cites)
    assert any("§481(a)" in c for c in r.pin_cites)


def test_implementation_steps_voluntary_change(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    steps = " ".join(r.implementation_steps)
    assert "Form 3115" in steps


def test_risks_warn_about_audit_protection(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "audit protection" in risks.lower() or "Rev. Rul. 90-38" in risks
