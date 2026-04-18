"""Tests for CHAR_PRE_SALE evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.CHARITABLE.CHAR_PRE_SALE import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_liquidity_event(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_liquidity_event_fixture(rules):
    """Liquidity fixture has planned event + appreciated S corp stock, residence,
    and portfolio."""
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["candidate_count"] >= 2


def test_qsbs_founder_with_liquidity_and_appreciated(rules):
    """QSBS founder fixture has planned liquidity + two QSBS lots that are
    appreciated + long-term (acquired 2022 and 2025-09)."""
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    # Pre-OBBBA lot 2022: year 2026 - 2022 = 4, LT qualifies
    # Post-OBBBA lot 2025-09: year 2026 - 2025 = 1, barely LT
    assert trace["candidate_count"] >= 1


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "CHAR_APPREC_SECURITIES" in result.cross_strategy_impacts
    assert "CHAR_DAF" in result.cross_strategy_impacts
    assert "SALE_BASIS_CLEANUP" in result.cross_strategy_impacts


def test_pin_cites_include_humacid_and_rev_rul(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("Humacid" in c for c in result.pin_cites)
    assert any("Rev. Rul. 78-197" in c for c in result.pin_cites)
    assert any("§170(e)(1)" in c for c in result.pin_cites)
    assert any("Ferguson" in c for c in result.pin_cites)


def test_total_benefit_sums_capgain_and_deduction(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    total = Decimal(trace["total_benefit"])
    avoided = Decimal(trace["avoided_cap_gain_tax"])
    deduction = Decimal(trace["deduction_value"])
    assert total == avoided + deduction
