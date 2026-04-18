"""Tests for SSALT_TRANSFER_TAX."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_TRANSFER_TAX import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable_with_real_property(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_not_applicable_without_real_property(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_single_1040.yaml").read_text())
    # single fixture has RSU_LOT_2025 (STOCK_PUBLIC), no real property
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert r.applicable is False


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "SSALT_NY_MANSION_TAX" in r.cross_strategy_impacts
    assert "SALE_M_AND_A_STRUCTURING" in r.cross_strategy_impacts


def test_pin_cites_include_ny_1402_and_la_ula(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("§1402" in c for c in r.pin_cites)
    assert any("Measure ULA" in c for c in r.pin_cites)


def test_assumptions_cover_la_ula_rates(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    text = " ".join(r.assumptions)
    assert "4%" in text and "5.5%" in text
