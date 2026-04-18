"""Tests for CAP_EXAMS_APPEALS."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_EXAMS_APPEALS import Evaluator
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
    assert "CAP_PENALTY_ABATEMENT" in r.cross_strategy_impacts
    assert "CAP_ACCOUNTING_METHOD_DEFENSE" in r.cross_strategy_impacts


def test_pin_cites_include_7602_7121_6330(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("§7602" in c for c in r.pin_cites)
    assert any("§7121" in c for c in r.pin_cites)
    assert any("§6330" in c for c in r.pin_cites)
    assert any("IRM 8" in c for c in r.pin_cites)


def test_risks_warn_about_90_day_letter(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "90-day" in risks or "Tax Court" in risks


def test_implementation_covers_fast_track(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    steps = " ".join(r.implementation_steps)
    assert "Fast Track" in steps
