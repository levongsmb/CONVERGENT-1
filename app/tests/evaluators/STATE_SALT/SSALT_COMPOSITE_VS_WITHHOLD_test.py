"""Tests for SSALT_COMPOSITE_VS_WITHHOLD."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_COMPOSITE_VS_WITHHOLD import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_pte(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_on_scorp(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True
    assert r.computation_trace["pte_entity_count"] == 1


def test_applicable_on_partnership(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "SSALT_PTET_MODELING" in r.cross_strategy_impacts
    assert "SSALT_NONRESIDENT_WH" in r.cross_strategy_impacts
    assert "SSALT_RESIDENT_CREDIT" in r.cross_strategy_impacts


def test_pin_cites_include_592_and_it203gr(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("592" in c for c in r.pin_cites)
    assert any("IT-203-GR" in c for c in r.pin_cites)
