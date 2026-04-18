"""Tests for SSALT_PTET_MODELING."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_PTET_MODELING import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_qualified_entity(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_on_ca_scorp(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True
    assert "CA" in r.computation_trace["ptet_state_exposures"]


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "CA_PTET_ELECTION" in r.cross_strategy_impacts
    assert "SSALT_164_SALT_CAP" in r.cross_strategy_impacts
    assert "SSALT_NY_PTET" in r.cross_strategy_impacts


def test_pin_cites(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("Notice 2020-75" in c for c in r.pin_cites)
    assert any("SB 132" in c for c in r.pin_cites)


def test_applicable_on_partnership(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    assert r.applicable is True
