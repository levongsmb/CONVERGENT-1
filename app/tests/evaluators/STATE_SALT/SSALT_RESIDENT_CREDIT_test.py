"""Tests for SSALT_RESIDENT_CREDIT."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_RESIDENT_CREDIT import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_multi_state(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_when_k1_has_pte_credit(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    assert "SSALT_PTET_MODELING" in r.cross_strategy_impacts
    assert "SSALT_NJ_RESIDENT_CREDIT" in r.cross_strategy_impacts


def test_pin_cites_include_wynne_and_ftb_1031(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    assert any("Wynne" in c for c in r.pin_cites)
    assert any("FTB Publication 1031" in c for c in r.pin_cites)


def test_risks_flag_double_credit(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    text = " ".join(r.risks_and_caveats)
    assert "PTET" in text and "resident credit" in text
