"""Tests for LL_163J_INTEREST evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.LOSS_LIMIT_NAVIGATION.LL_163J_INTEREST import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_large_entity_or_carryover(rules):
    scenario = _load("scenario_mfj_scorp_owner")  # gross receipts $1.6M, below threshold
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_when_carryover_present(rules):
    """Single fixture with synthetic §163(j) carryover."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["prior_year"]["suspended_163j_carryover"] = 75000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert result.computation_trace["has_carryover"] is True
    assert Decimal(result.computation_trace["prior_163j_carryover"]) == Decimal("75000")


def test_applicable_when_large_entity_above_threshold(rules):
    """Construct entity with gross receipts > $25M."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    for e in base["entities"]:
        if e["code"] == "SCORP_PRIMARY":
            e["gross_receipts_prior_3_avg"] = 28000000
            e["gross_receipts_prior_year"] = 32000000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert result.computation_trace["relevant_entity_count"] == 1


def test_cross_strategy_impacts_listed(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["prior_year"]["suspended_163j_carryover"] = 50000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "RED_163J_REPTOB" in result.cross_strategy_impacts
    assert "AM_448_GROSS_RECEIPTS" in result.cross_strategy_impacts
    assert "LL_163J_EBITDA_OBBBA" in result.cross_strategy_impacts


def test_pin_cites_include_163j_and_obbba(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["prior_year"]["suspended_163j_carryover"] = 50000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§163(j)" in c for c in result.pin_cites)
    assert any("EBITDA" in c for c in result.pin_cites)
    assert any("§448(c)" in c for c in result.pin_cites)
    assert any("§163(j)(7)(B)" in c for c in result.pin_cites)
