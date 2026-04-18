"""Tests for CAP_PAYROLL_REPORTING."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_PAYROLL_REPORTING import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_w2_employer(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_on_scorp_employer(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "COMP_PAYROLL_TAX_MIN" in r.cross_strategy_impacts
    assert "CAP_1099" in r.cross_strategy_impacts
    assert "COMP_WORKER_CLASSIFICATION" in r.cross_strategy_impacts


def test_pin_cites_include_6672_tfrp(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("§6672" in c for c in r.pin_cites)
    assert any("Form 941" in c for c in r.pin_cites)


def test_risks_warn_about_tfrp(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "§6672" in risks or "TFRP" in risks
