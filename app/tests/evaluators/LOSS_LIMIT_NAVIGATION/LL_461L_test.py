"""Tests for LL_461L evaluator."""

from __future__ import annotations

import copy
from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.LOSS_LIMIT_NAVIGATION.LL_461L import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules_patched():
    """Patched 2026 §461(l) threshold for deterministic test math."""
    base = ConfigRulesAdapter()
    ebl_real = base.get("federal/section_461l", 2026)
    ebl = copy.deepcopy(ebl_real)
    for p in ebl["parameters"]:
        sp = p["coordinate"].get("sub_parameter")
        if sp == "threshold_mfj":
            p["value"] = 625000
        if sp == "threshold_single_hoh_mfs":
            p["value"] = 310000

    class Patched:
        def get(self, key, year):
            return ebl if key == "federal/section_461l" else base.get(key, year)

        @property
        def version(self):
            return base.version

    return Patched()


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_when_no_business_loss(rules_patched):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules_patched, year=2026)
    assert result.applicable is False


def test_applicable_when_aggregate_business_loss(rules_patched):
    """Construct MFJ scenario with K-1 ordinary loss beyond threshold."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    # Convert S corp K-1 to big loss
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["ordinary_business_income"] = -1000000
            k1["qualified_business_income"] = 0

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules_patched, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["aggregate_business_loss"]) == Decimal("1000000")
    assert Decimal(trace["threshold"]) == Decimal("625000")
    assert Decimal(trace["allowed"]) == Decimal("625000")
    assert Decimal(trace["disallowed_to_nol"]) == Decimal("375000")


def test_low_confidence_when_threshold_null(rules):
    """Production cache has §461(l) threshold null -> degrade gracefully."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["ordinary_business_income"] = -500000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert result.verification_confidence == "low"


def test_cross_strategy_impacts_listed(rules_patched):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["ordinary_business_income"] = -2000000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules_patched, year=2026)
    assert "LL_NOL_USAGE" in result.cross_strategy_impacts
    assert "LL_SUSPENDED_LOSSES" in result.cross_strategy_impacts


def test_pin_cites_include_461l_and_obbba(rules_patched):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["ordinary_business_income"] = -2000000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules_patched, year=2026)
    assert any("§461(l)" in c for c in result.pin_cites)
    assert any("OBBBA" in c for c in result.pin_cites)
