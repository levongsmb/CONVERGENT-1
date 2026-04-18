"""Tests for CHAR_OBBBA_37_CAP evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.CHARITABLE.CHAR_OBBBA_37_CAP import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_itemized(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["deductions"] = {}
    base["deductions"]["charitable_cash_public"] = 0
    base["deductions"]["charitable_cash_daf"] = 0
    base["deductions"]["salt_paid_state_income"] = 0

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_not_applicable_below_37_bracket_threshold(rules):
    """MFJ S corp owner fixture: approx income $947K, itemized ~$75K (28.6K + 16.2K + 28.4K + 12K + 18K).
    Taxable income + itemized = $947K is above MFJ $768,700 threshold → applicable.
    Single fixture: income ~$149K, itemized ~$11.6K → $149K + $11.6K = $161K below single 37% threshold
    $640,600 → not applicable."""
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False
    assert "below the 37%" in result.reason


def test_applicable_on_scorp_owner_fixture(rules):
    """MFJ fixture is above 37% bracket, itemized is substantial."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["top_bracket_threshold"]) == Decimal("768700")
    assert Decimal(trace["total_itemized"]) > Decimal(0)
    assert Decimal(trace["reduction_to_itemized"]) > Decimal(0)


def test_reduction_mechanics_deterministic(rules):
    """Build a scenario where numbers are easy to check:
    MFJ, wages $1,200K, itemized $50K, no other income.
    Taxable income = $1,200K - $50K = $1,150K.
    Excess = $1,200K (inc + itemized = $1,200K) - $768,700 = $431,300.
    Limitation basis = min($50K, $431,300) = $50K.
    Reduction = $50K × 2/37 = $2,702.70.
    Tax cost at 37% = $1,000.00.
    """
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["income"]["wages_primary"] = 1200000
    base["income"]["wages_spouse"] = 0
    base["income"]["interest_ordinary"] = 0
    base["income"]["dividends_qualified"] = 0
    base["income"]["capital_gains_long_term"] = 0
    base["income"]["k1_income"] = []
    base["deductions"]["mortgage_interest_acquisition"] = 0
    base["deductions"]["salt_paid_state_income"] = 20000
    base["deductions"]["salt_paid_property_residence"] = 10000
    base["deductions"]["charitable_cash_public"] = 10000
    base["deductions"]["charitable_cash_daf"] = 10000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert Decimal(trace["total_itemized"]) == Decimal("50000")
    assert Decimal(trace["excess_over_threshold"]) == Decimal("431300")
    assert Decimal(trace["limitation_basis"]) == Decimal("50000")
    expected_reduction = (Decimal("50000") * Decimal(2) / Decimal(37)).quantize(Decimal("0.01"))
    assert Decimal(trace["reduction_to_itemized"]) == expected_reduction


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "CHAR_OBBBA_05_FLOOR" in result.cross_strategy_impacts
    assert "CHAR_BUNCHING" in result.cross_strategy_impacts
    assert "RET_CASH_BALANCE" in result.cross_strategy_impacts


def test_pin_cites_include_68_and_obbba(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§68" in c for c in result.pin_cites)
    assert any("§1(j)(2)" in c for c in result.pin_cites)
    assert any("OBBBA" in c for c in result.pin_cites)
