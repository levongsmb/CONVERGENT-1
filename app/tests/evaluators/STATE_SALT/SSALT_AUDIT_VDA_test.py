"""Tests for SSALT_AUDIT_VDA."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_AUDIT_VDA import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_business_activity(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_with_entity(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "SSALT_SALES_USE_EXPOSURE" in r.cross_strategy_impacts
    assert "CAP_STATUTE_MGMT" in r.cross_strategy_impacts
    assert "CAP_PENALTY_ABATEMENT" in r.cross_strategy_impacts


def test_pin_cites_include_mtc_and_ftb(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("Multistate Tax Commission" in c for c in r.pin_cites)
    assert any("§19191" in c for c in r.pin_cites)


def test_risks_warn_post_contact_unavailable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    text = " ".join(r.assumptions)
    assert "Post-contact" in text or "anonymous" in text.lower()
