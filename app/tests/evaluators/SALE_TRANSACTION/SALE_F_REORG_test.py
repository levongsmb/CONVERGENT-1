"""Tests for SALE_F_REORG evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.SALE_TRANSACTION.SALE_F_REORG import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_liquidity_event(rules):
    scenario = _load("scenario_mfj_scorp_owner")  # no liquidity event
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_not_applicable_without_scorp_target(rules):
    scenario = _load("scenario_qsbs_founder")  # C corp target + liquidity
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_liquidity_event_fixture(rules):
    """Liquidity fixture: S corp target, $18M proceeds, $1.85M basis.
    Gross gain = $16.15M.
    30% ordinary-equivalent = $4,845,000.
    Saving vs 338(h)(10) = $4,845,000 × (0.37 − 0.238) = $639,540.
    """
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["gross_gain"]) == Decimal("16150000")
    # 30% × 16,150,000 = 4,845,000
    # × (0.37 - 0.238) = 0.132
    # = 639,540
    assert Decimal(trace["proxy_recapture_portion_at_ordinary"]) == Decimal("4845000.00")
    assert Decimal(trace["estimated_saving_vs_338h10"]) == Decimal("639540.00")


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "SALE_ASSET_VS_STOCK" in result.cross_strategy_impacts
    assert "SALE_BASIS_CLEANUP" in result.cross_strategy_impacts
    assert "SCSI_F_REORG_SALE" in result.cross_strategy_impacts
    assert "SALE_338H10" in result.cross_strategy_impacts


def test_pin_cites_include_rev_rul_2008_18(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("Rev. Rul. 2008-18" in c for c in result.pin_cites)
    assert any("§368(a)(1)(F)" in c for c in result.pin_cites)
    assert any("§1361(b)(3)" in c for c in result.pin_cites)


def test_implementation_steps_cover_forms(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    steps = " ".join(result.implementation_steps)
    assert "Form 2553" in steps
    assert "Form 8869" in steps
    assert "F reorganization" in steps.lower() or "F-reorg" in steps
