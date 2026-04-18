"""Tests for CAP_1099."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_1099 import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_operating_entity(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_on_scorp(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "CAP_BACKUP_WITHHOLDING" in r.cross_strategy_impacts
    assert "CAP_W8_W9" in r.cross_strategy_impacts
    assert "COMP_WORKER_CLASSIFICATION" in r.cross_strategy_impacts


def test_pin_cites_include_6041_and_6050W(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("§6041" in c for c in r.pin_cites)
    assert any("§6050W" in c for c in r.pin_cites)
    assert any("Notice 2024-85" in c for c in r.pin_cites)


def test_assumptions_cover_1099_k_thresholds(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    a = " ".join(r.assumptions)
    assert "1099-NEC" in a
    assert "1099-K" in a
