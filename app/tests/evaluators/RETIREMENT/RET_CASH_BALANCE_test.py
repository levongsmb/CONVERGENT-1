"""Tests for RET_CASH_BALANCE evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.RETIREMENT.RET_CASH_BALANCE import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_below_income_floor(rules):
    scenario = _load("scenario_single_1040")  # W-2 $142K, no SE, not scorp
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_mfj_scorp_owner_45_55_band(rules):
    """Primary DOB 1980 → age 46 in 2026 → 45-55 band → target $150K."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["age_band"] == "45-55"
    assert Decimal(trace["target_contribution_rough"]) == Decimal("150000")
    # Fed save = 150000 * 35% = 52500
    assert result.estimated_tax_savings == Decimal("52500.00")


def test_55_60_band_on_liquidity_event_fixture(rules):
    """Liquidity fixture DOB 1968 → age 58 → 55-60 band → $225K target."""
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["age_band"] == "55-60"
    assert Decimal(trace["target_contribution_rough"]) == Decimal("225000")


def test_not_applicable_when_under_35(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["identity"]["primary_dob"] = "1995-01-01"  # age 31 in 2026

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False
    assert "< 35" in result.reason


def test_not_applicable_when_over_70(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["identity"]["primary_dob"] = "1950-01-01"  # age 76 in 2026

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False
    assert "> 70" in result.reason


def test_cross_strategy_impacts_listed(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "RET_SOLO_401K" in result.cross_strategy_impacts
    assert "RET_COMBO_PLANS" in result.cross_strategy_impacts
    assert "COMP_REASONABLE_COMP" in result.cross_strategy_impacts


def test_pin_cites_include_414j_and_415b(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§414(j)" in c for c in result.pin_cites)
    assert any("§415(b)" in c for c in result.pin_cites)
    assert any("Rev. Rul. 2002-42" in c for c in result.pin_cites)
