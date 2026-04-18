"""Tests for SET_SCORP_CONVERSION evaluator."""

from __future__ import annotations

import copy
from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.SELF_EMPLOYMENT_TAX.SET_SCORP_CONVERSION import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules_patched():
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


def test_not_applicable_when_scorp_already(rules_patched):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules_patched, year=2026)
    assert result.applicable is False


def test_not_applicable_below_breakeven(rules_patched):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["income"]["self_employment_income"] = 40000
    base["income"]["wages_primary"] = 0

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules_patched, year=2026)
    assert result.applicable is False


def test_applicable_with_200k_se_income(rules_patched):
    """$200K SE income: same math as ENT_SOLE_TO_SCORP.
    SE net = $184,700; current SE tax = $27,192.70; anchor comp = $73,880;
    post FICA = $11,303.64; gross save = $15,889.06."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["income"]["self_employment_income"] = 200000
    base["income"]["wages_primary"] = 0

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules_patched, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["current_se_tax"]) == Decimal("27192.70")
    assert Decimal(trace["reasonable_comp_anchor"]) == Decimal("73880.00")
    assert Decimal(trace["gross_saving"]) == Decimal("15889.06")


def test_low_confidence_when_oasdi_null():
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["income"]["self_employment_income"] = 200000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    real = ConfigRulesAdapter()
    result = Evaluator().evaluate(scenario, real, year=2026)
    assert result.applicable is True
    assert result.verification_confidence == "low"


def test_cross_strategy_impacts(rules_patched):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["income"]["self_employment_income"] = 200000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules_patched, year=2026)
    assert "ENT_SOLE_TO_SCORP" in result.cross_strategy_impacts
    assert "COMP_REASONABLE_COMP" in result.cross_strategy_impacts
    assert "QBI_SCORP_WAGE_BALANCE" in result.cross_strategy_impacts


def test_pin_cites_include_1402a2_and_rev_rul(rules_patched):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["income"]["self_employment_income"] = 200000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules_patched, year=2026)
    assert any("§1402(a)(2)" in c for c in result.pin_cites)
    assert any("Rev. Rul. 59-221" in c for c in result.pin_cites)
    assert any("§3101(b)(2)" in c for c in result.pin_cites)
