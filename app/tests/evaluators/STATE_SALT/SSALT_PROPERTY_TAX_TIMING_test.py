"""Tests for SSALT_PROPERTY_TAX_TIMING."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_PROPERTY_TAX_TIMING import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_when_no_property_tax(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_when_property_tax_paid(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "SSALT_164_SALT_CAP" in r.cross_strategy_impacts
    assert "CHAR_BUNCHING" in r.cross_strategy_impacts


def test_pin_cites_include_assessment_rule(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("§164(b)(6)" in c for c in r.pin_cites)
    assert any("§1.164-1" in c for c in r.pin_cites)
    assert any("assessment" in c.lower() for c in r.pin_cites)


def test_risks_flag_unassessed_prepayment(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    text = " ".join(r.risks_and_caveats)
    assert "not yet assessed" in text or "not deductible" in text.lower()
