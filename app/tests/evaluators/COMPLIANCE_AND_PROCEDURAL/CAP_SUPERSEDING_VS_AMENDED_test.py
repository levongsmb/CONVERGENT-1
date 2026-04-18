"""Tests for CAP_SUPERSEDING_VS_AMENDED."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_SUPERSEDING_VS_AMENDED import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert "CAP_STATUTE_MGMT" in r.cross_strategy_impacts
    assert "CAP_PROTECTIVE_ELECTIONS" in r.cross_strategy_impacts


def test_pin_cites_include_haggar(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("Haggar" in c for c in r.pin_cites)
    assert any("§6511" in c for c in r.pin_cites)
    assert any("§6501" in c for c in r.pin_cites)


def test_assumptions_cover_both_paths(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    a = " ".join(r.assumptions)
    assert "Superseding" in a
    assert "Amended" in a


def test_implementation_reference_forms(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    steps = " ".join(r.implementation_steps)
    assert "1040-X" in steps or "1120-X" in steps
