"""Tests for RED_COST_SEG evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.REAL_ESTATE_DEPRECIATION.RED_COST_SEG import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_real_property(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_real_estate_investor_fixture(rules):
    """Real-estate fixture has: commercial $2.25M placed 2025-11 + 2 residential
    rentals ($680K and $845K). Basis floor is $750K, so Rental A ($680K)
    is excluded. Candidates = Rental B + Commercial = 2."""
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["candidate_count"] == 2


def test_acceleration_computed_correctly(rules):
    """Commercial $2.25M × 25% = $562,500 reclassified.
    First-year bonus = $562,500.
    Baseline on reclassified under 39-year MACRS: 562500 / 39 / 2 = 7,211.54 (approx)
    Acceleration = 562500 - 7211.54 ≈ 555,288.46.
    Total across all three assets above $750K basis floor.
    """
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert Decimal(trace["total_first_year_acceleration"]) > Decimal(0)
    # Estimated fed save at 32%
    approx = Decimal(trace["total_first_year_acceleration"]) * Decimal("0.32")
    assert abs(result.estimated_tax_savings - approx.quantize(Decimal("0.01"))) <= Decimal("0.01")


def test_excludes_personal_residence(rules):
    """MFJ S-corp fixture has primary residence $945K basis but description
    is 'Primary residence, Burbank' — not flagged as rental → excluded.
    The fixture has no commercial property → not_applicable."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "RED_BONUS_DEPR" in result.cross_strategy_impacts
    assert "LL_REP_STATUS" in result.cross_strategy_impacts
    assert "LL_469_PASSIVE" in result.cross_strategy_impacts
    assert "CA_NONCONFORMITY_BONUS" in result.cross_strategy_impacts


def test_pin_cites_include_168k_and_obbba(rules):
    scenario = _load("scenario_real_estate_investor")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§168(k)" in c for c in result.pin_cites)
    assert any("OBBBA" in c for c in result.pin_cites)
    assert any("HCA" in c for c in result.pin_cites)
