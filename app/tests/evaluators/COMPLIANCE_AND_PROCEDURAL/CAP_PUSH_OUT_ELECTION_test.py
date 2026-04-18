"""Tests for CAP_PUSH_OUT_ELECTION."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_PUSH_OUT_ELECTION import Evaluator
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
    assert "CAP_BBA_AUDIT_REGIME" in r.cross_strategy_impacts
    assert "CAP_PR_CONTROLS" in r.cross_strategy_impacts


def test_pin_cites_include_6226(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    assert any("§6226" in c for c in r.pin_cites)
    assert any("§301.6226-1" in c for c in r.pin_cites)


def test_risks_cover_45_day_window(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    a = " ".join(r.assumptions)
    assert "45-day" in a or "45 days" in a
