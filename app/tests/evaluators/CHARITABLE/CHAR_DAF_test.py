"""Tests for CHAR_DAF evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.CHARITABLE.CHAR_DAF import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_charitable_giving(rules):
    """Single fixture has $2,400 charitable; still applicable. Partnership fixture has $6,200. Try real estate fixture which has $5,400."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["deductions"]["charitable_cash_public"] = 0
    base["deductions"]["charitable_cash_daf"] = 0

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_scorp_owner_with_daf_and_cash(rules):
    """MFJ S corp fixture: $12K cash + $18K DAF = $30K total."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["current_charitable_total"]) == Decimal("30000")
    # Fed save at 32% = $9,600
    assert result.estimated_tax_savings == Decimal("9600.00")


def test_applicable_on_liquidity_event_with_large_appreciated_gift(rules):
    """Liquidity fixture: $45K cash + $85K DAF + $125K appreciated = $255K."""
    scenario = _load("scenario_liquidity_event")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert Decimal(trace["current_charitable_total"]) == Decimal("255000")
    # Fed save at 32% = $81,600
    assert result.estimated_tax_savings == Decimal("81600.00")


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "CHAR_BUNCHING" in result.cross_strategy_impacts
    assert "CHAR_APPREC_SECURITIES" in result.cross_strategy_impacts
    assert "CHAR_OBBBA_05_FLOOR" in result.cross_strategy_impacts
    assert "CHAR_OBBBA_37_CAP" in result.cross_strategy_impacts


def test_pin_cites_include_170_provisions(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§170(b)(1)(A)" in c for c in result.pin_cites)
    assert any("§170(f)(18)" in c for c in result.pin_cites)
    assert any("OBBBA" in c for c in result.pin_cites)


def test_reads_standard_deduction_from_config(rules):
    calls = []

    class Spy:
        def __init__(self, w):
            self.w = w

        def get(self, k, y):
            calls.append((k, y))
            return self.w.get(k, y)

        @property
        def version(self):
            return self.w.version

    scenario = _load("scenario_mfj_scorp_owner")
    Evaluator().evaluate(scenario, Spy(rules), year=2026)
    assert ("federal/standard_deduction", 2026) in calls
