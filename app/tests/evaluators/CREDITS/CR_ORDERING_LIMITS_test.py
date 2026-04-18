"""Tests for CR_ORDERING_LIMITS evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.CREDITS.CR_ORDERING_LIMITS import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_when_low_tax_and_no_carryforwards(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["prior_year"]["total_federal_tax"] = 5000
    base["prior_year"]["credit_carryforwards"] = []

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_with_meaningful_tax(rules):
    """MFJ S corp owner fixture prior tax $192,300."""
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert Decimal(result.computation_trace["prior_year_federal_tax"]) == Decimal("192300.00")


def test_applicable_with_carryforward_credits(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["prior_year"]["total_federal_tax"] = 3000  # low tax
    base["prior_year"]["credit_carryforwards"] = [
        {"credit_type": "R&D", "amount": 25000, "year_generated": 2024, "expires": 2044},
    ]

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["has_carryforwards"] is True
    assert Decimal(trace["aggregate_carryforward_amount"]) == Decimal("25000")


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "CR_RND_41" in result.cross_strategy_impacts
    assert "CR_GBC_CARRYFWD" in result.cross_strategy_impacts
    assert "CR_STARTUP_PAYROLL_OFFSET" in result.cross_strategy_impacts


def test_pin_cites_include_38_and_39(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§38(a)" in c for c in result.pin_cites)
    assert any("§38(c)(1)" in c for c in result.pin_cites)
    assert any("§39(a)" in c for c in result.pin_cites)
    assert any("§38(d)" in c for c in result.pin_cites)
