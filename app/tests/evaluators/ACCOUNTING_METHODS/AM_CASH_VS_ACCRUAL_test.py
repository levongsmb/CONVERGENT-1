"""Tests for AM_CASH_VS_ACCRUAL evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.ACCOUNTING_METHODS.AM_CASH_VS_ACCRUAL import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_entity(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_not_applicable_when_entity_on_cash_already(rules):
    """MFJ S corp owner fixture: entity is on CASH already → no switch needed."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_when_accrual_entity_under_threshold(rules):
    """Liquidity fixture has ACCRUAL S corp with gross receipts $6.45M < $30M threshold."""
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["switch_candidate_count"] == 1
    candidate = trace["candidates"][0]
    assert candidate["entity_code"] == "SCORP_TARGET"
    assert candidate["current_method"] == "ACCRUAL"
    assert candidate["under_448c_proxy_threshold"] is True
    assert candidate["switch_candidate"] is True


def test_not_applicable_when_entity_above_threshold(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_liquidity_event.yaml").read_text()
    )
    # Push gross receipts above $30M threshold
    for e in base["entities"]:
        if e["code"] == "SCORP_TARGET":
            e["gross_receipts_prior_year"] = 50000000
            e["gross_receipts_prior_3_avg"] = 45000000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "AM_448_GROSS_RECEIPTS" in result.cross_strategy_impacts
    assert "AM_471C_INVENTORY" in result.cross_strategy_impacts
    assert "AM_481A_PLANNING" in result.cross_strategy_impacts


def test_pin_cites_include_446_and_448(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§446" in c for c in result.pin_cites)
    assert any("§448" in c for c in result.pin_cites)
    assert any("§471(c)" in c for c in result.pin_cites)
