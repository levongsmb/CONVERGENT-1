"""Tests for AM_174A_DOMESTIC_RE evaluator."""

from __future__ import annotations

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.ACCOUNTING_METHODS.AM_174A_DOMESTIC_RE import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_before_2025(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2024)
    assert result.applicable is False


def test_not_applicable_without_operating_entity(rules):
    scenario = _load("scenario_single_1040")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_applicable_on_scorp_owner_fixture(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert result.computation_trace["entities_potentially_affected"] == 1


def test_applicable_on_partnership_owner_fixture(rules):
    scenario = _load("scenario_partnership_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True


def test_cross_strategy_impacts(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "CR_RND_41" in result.cross_strategy_impacts
    assert "RND_280C_COORD" in result.cross_strategy_impacts
    assert "AM_481A_PLANNING" in result.cross_strategy_impacts


def test_pin_cites_include_174a_and_obbba(rules):
    scenario = _load("scenario_mfj_scorp_owner")
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§174A" in c for c in result.pin_cites)
    assert any("§70302" in c for c in result.pin_cites)
    assert any("§280C" in c for c in result.pin_cites)
    assert any("§481(a)" in c for c in result.pin_cites)
