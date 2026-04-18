"""Tests for CGL_1250_UNRECAPTURED evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.CAPITAL_GAINS_LOSSES.CGL_1250_UNRECAPTURED import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_1250_gain(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_with_direct_1250_gain(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["income"]["unrecaptured_1250_gain"] = 200000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["total_1250"]) == Decimal("200000")
    # Base tax at 25% = $50,000; NIIT at 3.8% = $7,600; total = $57,600
    assert Decimal(trace["base_1250_tax_at_25pct"]) == Decimal("50000.00")
    assert Decimal(trace["niit_component_at_3_8pct"]) == Decimal("7600.000")
    assert Decimal(trace["total_fed_on_1250"]) == Decimal("57600.00")


def test_applicable_with_k1_1250_gain(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["unrecaptured_1250_gain"] = 80000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert Decimal(result.computation_trace["k1_1250"]) == Decimal("80000")


def test_cross_strategy_impacts(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["income"]["unrecaptured_1250_gain"] = 100000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "RED_RECAPTURE_PLAN" in result.cross_strategy_impacts
    assert "RED1031_FORWARD" in result.cross_strategy_impacts
    assert "CGL_1231" in result.cross_strategy_impacts


def test_pin_cites_include_1h6_and_1250(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["income"]["unrecaptured_1250_gain"] = 100000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§1(h)(6)" in c for c in result.pin_cites)
    assert any("§1250" in c for c in result.pin_cites)
    assert any("§1031" in c for c in result.pin_cites)
    assert any("§453" in c for c in result.pin_cites)
