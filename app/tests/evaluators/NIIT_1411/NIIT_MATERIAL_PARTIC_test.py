"""Tests for NIIT_MATERIAL_PARTIC evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.NIIT_1411.NIIT_MATERIAL_PARTIC import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_k1_income(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_not_applicable_below_magi_threshold(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    # Squash wages and K-1 ordinary to below $250K MAGI
    base["income"]["wages_primary"] = 50000
    base["income"]["wages_spouse"] = 30000
    base["income"]["interest_ordinary"] = 0
    base["income"]["dividends_qualified"] = 0
    base["income"]["capital_gains_long_term"] = 0
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["ordinary_business_income"] = 100000
            k1["qualified_business_income"] = 100000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False
    assert "§1411(b) threshold" in result.reason


def test_applicable_on_scorp_owner_fixture(rules):
    """MFJ S corp fixture: MAGI ~$947K > $250K; K-1 ordinary $612K.
    Potential NIIT saving = $612K × 3.8% = $23,256."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["at_risk_income"]) == Decimal("612000")
    assert Decimal(trace["potential_niit_saving_if_nonpassive"]) == Decimal("23256.00")
    assert result.estimated_tax_savings == Decimal("23256.00")


def test_applicable_on_partnership_owner_fixture(rules):
    """Partnership fixture: MAGI ~$700K; K-1 ordinary $340K.
    Potential NIIT saving = $340K × 3.8% = $12,920."""
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["at_risk_income"]) == Decimal("340000")
    assert Decimal(trace["potential_niit_saving_if_nonpassive"]) == Decimal("12920.00")


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "NIIT_GROUPING" in result.cross_strategy_impacts
    assert "LL_469_PASSIVE" in result.cross_strategy_impacts
    assert "LL_REP_STATUS" in result.cross_strategy_impacts
    assert "SET_1402A13" in result.cross_strategy_impacts


def test_pin_cites_include_1411_and_469_regs(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§1411(a)" in c for c in result.pin_cites)
    assert any("§1411(c)(2)" in c for c in result.pin_cites)
    assert any("§1.469-5T(a)" in c for c in result.pin_cites)
    assert any("§1.1411-5" in c for c in result.pin_cites)
