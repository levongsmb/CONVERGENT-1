"""Tests for SSALT_STATE_ESTIMATES."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_STATE_ESTIMATES import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable_when_prior_state_tax(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True
    assert "CA" in r.computation_trace["exposed_states"]


def test_not_applicable_without_prior_state_tax(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_single_1040.yaml").read_text())
    base["prior_year"]["total_state_tax_by_state"] = {}
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert r.applicable is False


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "CAP_EST_TAX_SAFE_HARBORS" in r.cross_strategy_impacts
    assert "SSALT_PTET_MODELING" in r.cross_strategy_impacts


def test_pin_cites_include_ca_rtc_19136(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("§19136" in c for c in r.pin_cites)
    assert any("§685(c)" in c for c in r.pin_cites)


def test_assumptions_cover_ca_front_load(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    text = " ".join(r.assumptions)
    assert "30%" in text and "40%" in text
