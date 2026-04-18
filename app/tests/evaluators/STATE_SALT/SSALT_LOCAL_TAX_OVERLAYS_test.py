"""Tests for SSALT_LOCAL_TAX_OVERLAYS."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_LOCAL_TAX_OVERLAYS import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable_on_ca_scenario(rules):
    """CA is in the local-overlay list (SF GRT coverage)."""
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True
    assert "CA" in r.computation_trace["exposed_states"]


def test_not_applicable_without_overlay_state(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_single_1040.yaml").read_text())
    base["identity"]["primary_state_domicile"] = "FL"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert r.applicable is False


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "SSALT_NYC_RESIDENT" in r.cross_strategy_impacts
    assert "SSALT_SALES_USE_EXPOSURE" in r.cross_strategy_impacts


def test_pin_cites_include_ubt_and_grt(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("§11-503" in c for c in r.pin_cites)
    assert any("Article 12-A-1" in c for c in r.pin_cites)
    assert any("Act 32" in c for c in r.pin_cites)


def test_assumptions_cover_nyc_ubt_rate(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    text = " ".join(r.assumptions)
    assert "4%" in text
