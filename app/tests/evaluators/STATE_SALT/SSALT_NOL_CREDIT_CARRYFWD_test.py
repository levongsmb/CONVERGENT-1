"""Tests for SSALT_NOL_CREDIT_CARRYFWD."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_NOL_CREDIT_CARRYFWD import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_carryforward(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_when_pte_credit_carryforward(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "SSALT_CONFORMITY_DECOUPLING" in r.cross_strategy_impacts


def test_pin_cites_include_ca_17276_and_nol_suspension(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("§17276" in c for c in r.pin_cites)
    assert any("§24416" in c for c in r.pin_cites)
    assert any("§382" in c for c in r.pin_cites)


def test_assumptions_reference_ca_suspension_and_sb167(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    text = " ".join(r.assumptions)
    assert "SB 167" in text
    assert "suspended" in text.lower()
