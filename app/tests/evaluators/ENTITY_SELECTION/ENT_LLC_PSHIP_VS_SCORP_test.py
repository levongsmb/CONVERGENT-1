"""Tests for ENT_LLC_PSHIP_VS_SCORP evaluator."""

from __future__ import annotations

import copy
from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.ENTITY_SELECTION.ENT_LLC_PSHIP_VS_SCORP import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules_with_oasdi():
    base = ConfigRulesAdapter()
    fica_real = base.get("federal/fica_wage_bases", 2026)
    fica = copy.deepcopy(fica_real)
    for p in fica["parameters"]:
        if p["coordinate"].get("sub_parameter") == "oasdi_wage_base":
            p["value"] = 176100

    class Patched:
        def get(self, k, y):
            return fica if k == "federal/fica_wage_bases" else base.get(k, y)

        @property
        def version(self):
            return base.version

    return Patched()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_llc_partnership(rules_with_oasdi):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules_with_oasdi, year=2026)
    assert result.applicable is False


def test_applicable_on_partnership_owner_fixture(rules_with_oasdi):
    """Partnership fixture: $340K ordinary + $60K guaranteed = $400K share.
    SE net = 400000 * 0.9235 = 369,400.
    Current SE = min(369400, 176100) * 0.124 + 369400 * 0.029
      = 21836.40 + 10712.60 = 32549.00.
    Reasonable comp = 400000 * 0.40 = 160000.
    Post FICA = min(160000, 176100) * 0.124 + 160000 * 0.029
      = 19840.00 + 4640.00 = 24480.00.
    Gross savings = 32549.00 - 24480.00 = 8069.00.
    Net after $5K compliance = 3069.00.
    """
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules_with_oasdi, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["distributive_share"]) == Decimal("400000")
    assert Decimal(trace["current_se_tax"]) == Decimal("32549.00")
    assert Decimal(trace["reasonable_comp_anchor"]) == Decimal("160000.00")
    assert Decimal(trace["post_conversion_fica"]) == Decimal("24480.00")
    assert Decimal(trace["net_savings"]) == Decimal("3069.00")


def test_degrades_when_oasdi_base_null():
    scenario = _load("scenario_partnership_owner")
    real_rules = ConfigRulesAdapter()
    result = Evaluator().evaluate(scenario, real_rules, year=2026)
    assert result.applicable is True
    assert result.verification_confidence == "low"


def test_cross_strategy_impacts(rules_with_oasdi):
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules_with_oasdi, year=2026)
    assert "SET_SOROBAN_RISK" in result.cross_strategy_impacts
    assert "COMP_REASONABLE_COMP" in result.cross_strategy_impacts
    assert "PS_SPECIAL_ALLOCATIONS" in result.cross_strategy_impacts


def test_pin_cites_include_check_the_box_and_soroban(rules_with_oasdi):
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules_with_oasdi, year=2026)
    assert any("§7701" in c for c in result.pin_cites)
    assert any("§301.7701-3" in c for c in result.pin_cites)
    assert any("Soroban" in c for c in result.pin_cites)
