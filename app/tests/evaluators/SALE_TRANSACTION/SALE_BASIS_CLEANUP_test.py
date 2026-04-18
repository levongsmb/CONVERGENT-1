"""Tests for SALE_BASIS_CLEANUP evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.SALE_TRANSACTION.SALE_BASIS_CLEANUP import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_liquidity_event(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_liquidity_event_fixture(rules):
    """Liquidity fixture has S corp with AAA $3.12M and legacy AE&P $480K."""
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    # One entity findings
    assert len(trace["findings"]) == 1
    f = trace["findings"][0]
    assert f["entity_code"] == "SCORP_TARGET"
    # Expect AAA item + AE&P item (at minimum)
    aaa_flagged = any("AAA balance" in item for item in f["cleanup_items"])
    aep_flagged = any("Accumulated E&P" in item for item in f["cleanup_items"])
    assert aaa_flagged
    assert aep_flagged


def test_partnership_target_flags_754_posture(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_partnership_owner.yaml").read_text()
    )
    base["planning"]["liquidity_event_planned"] = {
        "target_close_date": "2028-03-31",
        "expected_proceeds": 25000000,
    }
    base["planning"]["objectives"] = ["LIQUIDITY_EVENT_PREP", "MINIMIZE_LIFETIME"]

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    f = trace["findings"][0]
    assert any("§754 election" in item for item in f["cleanup_items"])


def test_suspended_losses_surfaced(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_liquidity_event.yaml").read_text()
    )
    base["prior_year"]["suspended_passive_losses"] = 85000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    f = trace["findings"][0]
    assert any("Suspended passive losses" in item for item in f["cleanup_items"])


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "SALE_F_REORG" in result.cross_strategy_impacts
    assert "PTE_AAA_TRACKING" in result.cross_strategy_impacts
    assert "SCSI_BIG_1374" in result.cross_strategy_impacts
    assert "LL_DISPOSITION_FREE_SL" in result.cross_strategy_impacts


def test_pin_cites_include_1368_and_754(rules):
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§1368" in c for c in result.pin_cites)
    assert any("§754" in c for c in result.pin_cites)
    assert any("§1366(d)" in c for c in result.pin_cites)
    assert any("§7872" in c for c in result.pin_cites)
