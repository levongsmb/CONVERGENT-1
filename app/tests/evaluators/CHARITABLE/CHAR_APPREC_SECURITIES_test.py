"""Tests for CHAR_APPREC_SECURITIES evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.CHARITABLE.CHAR_APPREC_SECURITIES import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_appreciated_public_stock(rules):
    scenario = _load("scenario_mfj_scorp_owner")  # only residence
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_liquidity_fixture_portfolio(rules):
    """Liquidity fixture: INVEST_PORTFOLIO_LT is STOCK_PUBLIC with $750K gain,
    acquired 2018 → 8 years held."""
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["candidate_count"] == 1
    assert Decimal(trace["aggregate_unrealized_gain"]) == Decimal("750000")


def test_excludes_short_term_holdings(rules):
    """Single fixture: RSU acquired 2025-08 — 2026 year = 1-year hold
    (acquisition year 2025, year = 2026, years_held = 1). Edge case."""
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    # Per evaluator: years_held < 1 excludes; years_held = 1 includes.
    # RSU acquisition year is 2025, so years_held = 1 in 2026 → included.
    assert result.applicable is True


def test_excludes_private_stock(rules):
    """QSBS founder fixture stock is STOCK_QSBS, not STOCK_PUBLIC → excluded."""
    scenario = _load("scenario_qsbs_founder")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "CHAR_DAF" in result.cross_strategy_impacts
    assert "CHAR_PRE_SALE" in result.cross_strategy_impacts
    assert "CHAR_AGI_LIMITS" in result.cross_strategy_impacts


def test_pin_cites_include_170e1(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§170(e)(1)(A)" in c for c in result.pin_cites)
    assert any("§170(b)(1)(C)" in c for c in result.pin_cites)
    assert any("§170(b)(1)(D)" in c for c in result.pin_cites)
