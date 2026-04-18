"""Tests for SET_1402A13 evaluator."""

from __future__ import annotations

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.SELF_EMPLOYMENT_TAX.SET_1402A13 import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_partnership_k1(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_partnership_fixture(rules):
    """Partnership fixture: SE earnings $400K (full distributive share treated as SE).
    Exception not claimed → SOROBAN_CONSERVATIVE risk posture."""
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["partnership_k1_count"] == 1
    assert trace["any_full_distributive_se"] is True
    assert "SOROBAN_CONSERVATIVE" in trace["risk_posture"]


def test_high_risk_when_exception_appears_claimed(rules):
    """Construct a scenario where the LLC member has $340K ordinary + $60K GP
    but SE earnings = $60K (only GP treated as SE)."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_partnership_owner.yaml").read_text()
    )
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "LLC_PARTNERSHIP_MAIN":
            k1["self_employment_earnings"] = 60000  # only GP portion

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert trace["any_exception_claimed"] is True
    assert "HIGH_RISK" in trace["risk_posture"]


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "SET_SCORP_CONVERSION" in result.cross_strategy_impacts
    assert "SET_SOROBAN_RISK" in result.cross_strategy_impacts
    assert "ENT_LLC_PSHIP_VS_SCORP" in result.cross_strategy_impacts
    assert "NIIT_MATERIAL_PARTIC" in result.cross_strategy_impacts


def test_pin_cites_include_soroban_and_prop_reg(rules):
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("Soroban" in c for c in result.pin_cites)
    assert any("Denham" in c for c in result.pin_cites)
    assert any("§1402(a)(13)" in c for c in result.pin_cites)
    assert any("Prop. Treas. Reg." in c for c in result.pin_cites)


def test_implementation_steps_cover_functional_test(rules):
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    steps = " ".join(result.implementation_steps)
    assert "Soroban" in steps
    assert "Form 8275" in steps
