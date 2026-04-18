"""Tests for SSALT_NONRESIDENT_WH."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_NONRESIDENT_WH import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_pte(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_on_scorp(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_partnership_owner.yaml"), rules, 2026)
    assert "SSALT_PTET_MODELING" in r.cross_strategy_impacts
    assert "SSALT_COMPOSITE_VS_WITHHOLD" in r.cross_strategy_impacts


def test_pin_cites(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("§18662" in c for c in r.pin_cites)
    assert any("§658(c)(4)" in c for c in r.pin_cites)


def test_steps_mention_589_or_588(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    a = " ".join(r.assumptions)
    assert "589" in a or "588" in a
