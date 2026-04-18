"""Tests for CAP_FORM_8308."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_FORM_8308 import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_partnership(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_on_partnership(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    assert "PS_751_HOT_ASSETS" in r.cross_strategy_impacts
    assert "PTE_754_ELECTION" in r.cross_strategy_impacts


def test_pin_cites_include_6050K_and_751a(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    assert any("§6050K" in c for c in r.pin_cites)
    assert any("§1.6050K-1" in c for c in r.pin_cites)
    assert any("§751(a)" in c for c in r.pin_cites)


def test_implementation_cover_distribution_dates(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    steps = " ".join(r.implementation_steps)
    assert "January 31" in steps
    assert "3/15" in steps or "March" in steps.lower()
