"""Tests for ENT_SOLE_TO_SCORP evaluator."""

from __future__ import annotations

import copy
from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.ENTITY_SELECTION.ENT_SOLE_TO_SCORP import Evaluator
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


def test_not_applicable_when_scorp_already_present(rules_with_oasdi):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules_with_oasdi, year=2026)
    assert result.applicable is False
    assert "already has an S corp" in result.reason


def test_not_applicable_below_breakeven_floor(rules_with_oasdi):
    """$50K SE income is below $60K breakeven floor."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["income"]["self_employment_income"] = 50000
    base["income"]["wages_primary"] = 0

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules_with_oasdi, year=2026)
    assert result.applicable is False


def test_applicable_and_computes_net_savings(rules_with_oasdi):
    """$200K SE income: SE net = 200000 * 0.9235 = 184,700.
    Current SE tax on $184,700: OASDI on min(184,700, 176,100) = 176,100 * 12.4% = $21,836.40
    Medicare: 184,700 * 2.9% = $5,356.30. Total SE = $27,192.70.
    Reasonable comp anchor: 184,700 * 40% = $73,880.
    Post-conversion FICA: OASDI on min(73,880, 176,100) = 73,880 * 12.4% = $9,161.12
    Medicare: 73,880 * 2.9% = $2,142.52. Total post = $11,303.64.
    Gross savings = $27,192.70 - $11,303.64 = $15,889.06.
    Net after compliance = $15,889.06 - $3,500 = $12,389.06.
    """
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["income"]["self_employment_income"] = 200000
    base["income"]["wages_primary"] = 0

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules_with_oasdi, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["se_net_after_multiplier"]) == Decimal("184700.0000")
    assert Decimal(trace["current_se_tax"]) == Decimal("27192.70")
    assert Decimal(trace["assumed_reasonable_comp"]) == Decimal("73880.00")
    assert Decimal(trace["net_savings"]) == Decimal("12389.06")
    assert result.estimated_tax_savings == Decimal("12389.06")


def test_degrades_when_oasdi_base_null():
    """Real rules cache has OASDI null → low confidence."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["income"]["self_employment_income"] = 200000
    base["income"]["wages_primary"] = 0

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    real_rules = ConfigRulesAdapter()
    result = Evaluator().evaluate(scenario, real_rules, year=2026)
    assert result.applicable is True
    assert result.verification_confidence == "low"


def test_cross_strategy_impacts(rules_with_oasdi):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["income"]["self_employment_income"] = 200000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules_with_oasdi, year=2026)
    assert "COMP_REASONABLE_COMP" in result.cross_strategy_impacts
    assert "QBI_SCORP_WAGE_BALANCE" in result.cross_strategy_impacts
    assert "RET_SOLO_401K" in result.cross_strategy_impacts


def test_pin_cites_include_scorp_and_1402(rules_with_oasdi):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["income"]["self_employment_income"] = 200000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules_with_oasdi, year=2026)
    assert any("§1361" in c for c in result.pin_cites)
    assert any("§1402(a)" in c for c in result.pin_cites)
    assert any("Rev. Rul. 59-221" in c for c in result.pin_cites)
