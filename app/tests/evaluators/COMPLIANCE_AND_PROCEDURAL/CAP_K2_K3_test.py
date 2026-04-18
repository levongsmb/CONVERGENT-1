"""Tests for CAP_K2_K3."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_K2_K3 import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_flowthrough(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_on_scorp(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_applicable_on_partnership(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "IO_5471_5472" in r.cross_strategy_impacts
    assert "IO_FTC_BASKETS" in r.cross_strategy_impacts


def test_pin_cites_include_dfe(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("Schedule K-2" in c for c in r.pin_cites)
    assert any("Domestic Filing Exception" in c for c in r.pin_cites)


def test_assumptions_cover_dfe_conditions(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    a = " ".join(r.assumptions)
    assert "Domestic Filing Exception" in a or "DFE" in a
