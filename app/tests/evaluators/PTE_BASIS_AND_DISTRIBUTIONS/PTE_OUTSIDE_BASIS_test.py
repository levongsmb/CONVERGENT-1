"""Tests for PTE_OUTSIDE_BASIS evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.PTE_BASIS_AND_DISTRIBUTIONS.PTE_OUTSIDE_BASIS import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_partnership(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_partnership_owner_fixture(rules):
    """Partnership fixture: outside_basis $215,000 populated → no missing."""
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["partnership_count"] == 1
    f = trace["findings"][0]
    assert f["entity_code"] == "LLC_PARTNERSHIP_MAIN"
    assert f["missing_outside_basis"] is False
    assert Decimal(f["outside_basis"]) == Decimal("215000")


def test_flags_missing_outside_basis(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_partnership_owner.yaml").read_text()
    )
    for e in base["entities"]:
        if e["code"] == "LLC_PARTNERSHIP_MAIN":
            e["outside_basis"] = None

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert trace["any_missing_outside_basis"] is True


def test_surfaces_suspended_704d_carryover(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_partnership_owner.yaml").read_text()
    )
    base["prior_year"]["suspended_704d_carryover"] = 45000

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert Decimal(trace["suspended_704d_carryover"]) == Decimal("45000")


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "PTE_704D_LIMITATION" in result.cross_strategy_impacts
    assert "PTE_754_ELECTION" in result.cross_strategy_impacts
    assert "LL_465_AT_RISK" in result.cross_strategy_impacts
    assert "SALE_751_HOT_ASSETS" in result.cross_strategy_impacts


def test_pin_cites_include_705_752_731(rules):
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§705(a)" in c for c in result.pin_cites)
    assert any("§752" in c for c in result.pin_cites)
    assert any("§704(d)" in c for c in result.pin_cites)
    assert any("§731" in c for c in result.pin_cites)
