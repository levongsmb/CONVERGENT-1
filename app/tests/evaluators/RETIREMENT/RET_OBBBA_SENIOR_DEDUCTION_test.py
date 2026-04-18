"""Tests for RET_OBBBA_SENIOR_DEDUCTION evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.RETIREMENT.RET_OBBBA_SENIOR_DEDUCTION import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_outside_sunset_window(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2029)
    assert result.applicable is False
    assert "2025-2028" in result.reason


def test_not_applicable_under_65(rules):
    scenario = _load("scenario_mfj_scorp_owner")  # primary age 46 in 2026
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False
    assert "age 65" in result.reason


def test_single_qualifying_taxpayer_with_low_magi(rules):
    """Age 67 single with MAGI $50K: below $75K threshold → full $6,000."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["identity"]["primary_dob"] = "1959-01-01"
    base["income"]["wages_primary"] = 45000
    base["income"]["interest_ordinary"] = 2000
    base["income"]["dividends_qualified"] = 1000
    base["income"]["capital_gains_long_term"] = 0

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["qualifying_count"] == 1
    assert Decimal(trace["allowed_deduction"]) == Decimal("6000.00")
    # 6000 * 22% = 1320
    assert result.estimated_tax_savings == Decimal("1320.00")


def test_mfj_both_65plus_doubles_deduction(rules):
    """Both spouses 65+, MAGI below threshold → $12,000 gross deduction."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["identity"]["primary_dob"] = "1959-01-01"
    base["identity"]["spouse_dob"] = "1960-01-01"
    base["income"]["wages_primary"] = 50000
    base["income"]["wages_spouse"] = 40000
    base["income"]["interest_ordinary"] = 0
    base["income"]["dividends_qualified"] = 0
    base["income"]["capital_gains_long_term"] = 0
    base["income"]["k1_income"] = []

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert trace["qualifying_count"] == 2
    assert Decimal(trace["gross_deduction"]) == Decimal("12000")
    assert Decimal(trace["allowed_deduction"]) == Decimal("12000.00")


def test_phaseout_reduces_deduction(rules):
    """MFJ both 65+, MAGI $200K = $50K over $150K threshold → phaseout
    $50,000 × 6% = $3,000 reduction → deduction $12K - $3K = $9K."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["identity"]["primary_dob"] = "1959-01-01"
    base["identity"]["spouse_dob"] = "1960-01-01"
    base["income"]["wages_primary"] = 100000
    base["income"]["wages_spouse"] = 100000
    base["income"]["interest_ordinary"] = 0
    base["income"]["dividends_qualified"] = 0
    base["income"]["capital_gains_long_term"] = 0
    base["income"]["k1_income"] = []

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert Decimal(trace["magi"]) == Decimal("200000")
    assert Decimal(trace["phaseout_reduction"]) == Decimal("3000.00")
    assert Decimal(trace["allowed_deduction"]) == Decimal("9000.00")


def test_cross_strategy_impacts(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["identity"]["primary_dob"] = "1959-01-01"

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "RET_ROTH_CONVERSION" in result.cross_strategy_impacts
    assert "CA_PTET_ELECTION" in result.cross_strategy_impacts


def test_pin_cites_include_151f_and_obbba(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["identity"]["primary_dob"] = "1959-01-01"

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§151(f)" in c for c in result.pin_cites)
    assert any("OBBBA" in c for c in result.pin_cites)
