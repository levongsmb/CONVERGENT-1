"""Tests for SSALT_SALES_USE_EXPOSURE."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_SALES_USE_EXPOSURE import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_business_or_event(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_with_business(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "SSALT_AUDIT_VDA" in r.cross_strategy_impacts
    assert "SSALT_TRANSFER_TAX" in r.cross_strategy_impacts


def test_pin_cites_include_wayfair(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("Wayfair" in c for c in r.pin_cites)
    assert any("§6203" in c for c in r.pin_cites)


def test_risks_flag_successor_liability(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    text = " ".join(r.risks_and_caveats)
    assert "successor" in text.lower()
