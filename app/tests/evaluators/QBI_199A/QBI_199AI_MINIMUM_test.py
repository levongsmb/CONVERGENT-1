"""Tests for QBI_199AI_MINIMUM evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.QBI_199A.QBI_199AI_MINIMUM import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_active_qbi(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_not_applicable_below_1000_active_qbi(rules):
    """Construct a scenario with tiny QBI ($500) - below $1,000 threshold."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["qualified_business_income"] = 500
            k1["ordinary_business_income"] = 500

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False
    assert "$1,000" in result.reason


def test_floor_binds_at_low_qbi(rules):
    """Construct a scenario with QBI = $1,500 - below $400 floor since 20% * $1,500 = $300."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["qualified_business_income"] = 1500
            k1["ordinary_business_income"] = 1500

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["minimum_binds"] is True
    # 20% * 1500 = 300; delta = 400 - 300 = 100
    assert Decimal(trace["computed_deduction_20pct"]) == Decimal("300.00")
    assert Decimal(trace["delta_to_floor"]) == Decimal("100")
    # Tax saving = 100 * 22% = 22.00
    assert result.estimated_tax_savings == Decimal("22.00")


def test_floor_does_not_bind_on_scorp_owner_fixture(rules):
    """Primary fixture has $612K QBI; 20% = $122,400 >> $400 floor."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["minimum_binds"] is False
    assert Decimal(trace["delta_to_floor"]) == Decimal(0)
    assert result.estimated_tax_savings == Decimal(0)


def test_cross_strategy_impacts_listed(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "QBI_ACTIVE_TB_QUAL" in result.cross_strategy_impacts
    assert "QBI_MATERIAL_PARTIC_MIN" in result.cross_strategy_impacts
    assert "LL_469_PASSIVE" in result.cross_strategy_impacts


def test_pin_cites_include_199a_i_and_obbba(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§199A(i)" in c for c in result.pin_cites)
    assert any("§70431" in c for c in result.pin_cites)


def test_partnership_k1_with_se_earnings_is_active(rules):
    """Partnership fixture has SE earnings > 0 -> counts as active."""
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["active_k1_count"] == 1
