"""Tests for CAP_ERC_DEFENSE."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_ERC_DEFENSE import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert "CAP_EXAMS_APPEALS" in r.cross_strategy_impacts
    assert "CAP_PENALTY_ABATEMENT" in r.cross_strategy_impacts


def test_pin_cites_include_cares_and_notices(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert any("CARES Act" in c for c in r.pin_cites)
    assert any("Notice 2021-20" in c for c in r.pin_cites)
    assert any("IR-2023-169" in c for c in r.pin_cites)
    assert any("IR-2024-203" in c for c in r.pin_cites)


def test_implementation_covers_vdp(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    steps = " ".join(r.implementation_steps)
    assert "VDP 2.0" in steps or "voluntary disclosure" in steps.lower()


def test_risks_warn_75pct(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    risks = " ".join(r.risks_and_caveats)
    assert "75%" in risks or "§6694" in risks
