"""Tests for CAP_3115_METHOD_CHANGE."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_3115_METHOD_CHANGE import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy_covers_method_families(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert "AM_481A_PLANNING" in r.cross_strategy_impacts
    assert "AM_CASH_VS_ACCRUAL" in r.cross_strategy_impacts
    assert "RED_COST_SEG" in r.cross_strategy_impacts


def test_pin_cites_include_rev_procs(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("Rev. Proc. 2015-13" in c for c in r.pin_cites)
    assert any("Rev. Proc. 2023-24" in c for c in r.pin_cites)
    assert any("§446(e)" in c for c in r.pin_cites)


def test_implementation_steps_cover_duplicate_filing(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    steps = " ".join(r.implementation_steps)
    assert "Ogden" in steps
    assert "DCN" in steps


def test_risks_warn_about_classification(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "method change" in risks.lower()
