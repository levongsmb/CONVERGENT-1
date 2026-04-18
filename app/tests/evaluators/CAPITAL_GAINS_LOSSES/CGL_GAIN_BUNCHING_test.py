"""Tests for CGL_GAIN_BUNCHING evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.CAPITAL_GAINS_LOSSES.CGL_GAIN_BUNCHING import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_unrealized_gains(rules):
    """Partnership fixture has no securities positions tracked → not applicable."""
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_when_unrealized_gains_present(rules):
    """Liquidity fixture: INVEST_PORTFOLIO_LT $1.4M basis / $2.15M FMV = $750K gain."""
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["total_unrealized_gain"]) == Decimal("750000")


def test_single_1040_rsu_gain_surfaced(rules):
    """Single fixture RSU: $18,400 basis / $24,900 FMV = $6,500 gain."""
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert Decimal(result.computation_trace["total_unrealized_gain"]) == Decimal("6500")


def test_low_confidence_when_breakpoints_null(rules):
    """Current rules cache has §1(h) bracket breakpoints null → low confidence."""
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.verification_confidence == "low"


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "CGL_TAX_LOSS_HARVEST" in result.cross_strategy_impacts
    assert "NIIT_CAP_GAIN_HARVEST" in result.cross_strategy_impacts
    assert "RD_CA_DOMICILE_BREAK" in result.cross_strategy_impacts


def test_pin_cites_include_1h_and_1411(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§1(h)" in c for c in result.pin_cites)
    assert any("§1411" in c for c in result.pin_cites)
    assert any("Rev. Proc. 2025-32" in c for c in result.pin_cites)
