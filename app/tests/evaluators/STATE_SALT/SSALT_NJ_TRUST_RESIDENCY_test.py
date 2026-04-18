"""Tests for SSALT_NJ_TRUST_RESIDENCY."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_NJ_TRUST_RESIDENCY import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_trust(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_with_trust(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_trust_beneficiary.yaml"), rules, 2026)
    assert r.applicable is True
    assert r.computation_trace["trust_count"] == 1


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_trust_beneficiary.yaml"), rules, 2026)
    assert "EST_TRUST_SITUS" in r.cross_strategy_impacts
    assert "SSALT_NJ_BAIT" in r.cross_strategy_impacts


def test_pin_cites_include_kassner_and_residuary(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_trust_beneficiary.yaml"), rules, 2026)
    assert any("Kassner" in c for c in r.pin_cites)
    assert any("Residuary Trust A" in c for c in r.pin_cites)
    assert any("54A:1-2(o)" in c for c in r.pin_cites)


def test_assumptions_cover_kassner_three_prong(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_trust_beneficiary.yaml"), rules, 2026)
    text = " ".join(r.implementation_steps + r.assumptions)
    assert "three-prong" in text or "trustee" in text.lower()
