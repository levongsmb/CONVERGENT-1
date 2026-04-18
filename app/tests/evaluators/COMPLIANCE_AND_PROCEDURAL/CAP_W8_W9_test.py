"""Tests for CAP_W8_W9."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_W8_W9 import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_entity(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_on_scorp(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "II_FDAP" in r.cross_strategy_impacts
    assert "II_TREATY_BENEFITS" in r.cross_strategy_impacts
    assert "II_1441_1442" in r.cross_strategy_impacts


def test_pin_cites_include_1441_1471(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("§1441" in c for c in r.pin_cites)
    assert any("§1471" in c for c in r.pin_cites)
    assert any("W-8BEN-E" in c for c in r.pin_cites)


def test_risks_treaty_requirements(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "LOB" in risks or "Treaty" in risks or "treaty" in risks
