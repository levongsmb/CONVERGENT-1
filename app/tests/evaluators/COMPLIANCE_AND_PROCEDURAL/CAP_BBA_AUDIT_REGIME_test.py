"""Tests for CAP_BBA_AUDIT_REGIME."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_BBA_AUDIT_REGIME import Evaluator
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
    assert "CAP_PUSH_OUT_ELECTION" in r.cross_strategy_impacts
    assert "CAP_PR_CONTROLS" in r.cross_strategy_impacts


def test_pin_cites_include_bba_sections(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    assert any("§6221" in c for c in r.pin_cites)
    assert any("§6223" in c for c in r.pin_cites)
    assert any("§6226" in c for c in r.pin_cites)


def test_risks_flag_llc_partner_block(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "LLC" in risks or "single-member" in risks.lower()
