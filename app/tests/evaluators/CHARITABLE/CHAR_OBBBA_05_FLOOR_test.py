"""Tests for CHAR_OBBBA_05_FLOOR evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.CHARITABLE.CHAR_OBBBA_05_FLOOR import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_before_2026(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2025)
    assert result.applicable is False


def test_not_applicable_without_charitable(rules):
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


def test_floor_applied_to_scorp_owner_fixture(rules):
    """MFJ S corp owner: approx AGI ~$947K, 0.5% = $4,740.
    Total charitable = $12K + $18K = $30K.
    Disallowed = min($30K, $4,740) = $4,740.
    Allowed = $30K - $4,740 = $25,260.
    Tax drag at 32% = $1,516.80.
    """
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["floor_amount"]) == Decimal("4739.70")
    assert Decimal(trace["total_itemized_charitable"]) == Decimal("30000")
    assert Decimal(trace["disallowed_to_carryforward"]) == Decimal("4739.70")
    assert Decimal(trace["allowed_current_year"]) == Decimal("25260.30")


def test_floor_caps_at_total_charitable_when_charitable_less_than_floor(rules):
    """Single fixture: AGI $149,410 × 0.5% = $747.05. Charitable $2,400 > floor.
    Disallowed = floor = $747.05, allowed = $2,400 - $747.05 = $1,652.95.
    """
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["floor_amount"]) == Decimal("747.05")


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "CHAR_BUNCHING" in result.cross_strategy_impacts
    assert "CHAR_DAF" in result.cross_strategy_impacts
    assert "CHAR_OBBBA_CORPORATE_FLOOR" in result.cross_strategy_impacts


def test_pin_cites_include_170a_and_obbba(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§170(a)" in c for c in result.pin_cites)
    assert any("§170(d)" in c for c in result.pin_cites)
    assert any("OBBBA" in c for c in result.pin_cites)
