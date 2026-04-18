"""Tests for CGL_1231 evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.CAPITAL_GAINS_LOSSES.CGL_1231 import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_1231_activity(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_net_1231_gain_treated_as_ltcg(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["section_1231_gain"] = 100000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert Decimal(trace["total_section_1231"]) == Decimal("100000")
    assert trace["character"] == "LTCG"
    # Differential = $100K × (0.37 - 0.238) = 13,200
    assert Decimal(trace["rate_differential_saving"]) == Decimal("13200.00")


def test_net_1231_loss_treated_as_ordinary(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["section_1231_gain"] = -50000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert trace["character"] == "ORDINARY_LOSS"
    # Differential = $50K × 0.37 = 18,500
    assert Decimal(trace["rate_differential_saving"]) == Decimal("18500.00")


def test_cross_strategy_impacts(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["section_1231_gain"] = 75000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "CGL_1250_UNRECAPTURED" in result.cross_strategy_impacts
    assert "RED_RECAPTURE_PLAN" in result.cross_strategy_impacts


def test_pin_cites_include_1231_subsections(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    for k1 in base["income"]["k1_income"]:
        if k1["entity_code"] == "SCORP_PRIMARY":
            k1["section_1231_gain"] = 75000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§1231(a)(1)" in c for c in result.pin_cites)
    assert any("§1231(a)(2)" in c for c in result.pin_cites)
    assert any("§1231(c)" in c for c in result.pin_cites)
