"""Tests for SSALT_NJ_BAIT."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_NJ_BAIT import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_nj_pte(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_with_nj_pte(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "NJ"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "NJ"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert "SSALT_NJ_RESIDENT_CREDIT" in r.cross_strategy_impacts
    assert "SSALT_PTET_MODELING" in r.cross_strategy_impacts


def test_pin_cites_include_bait_statute(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "NJ"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert any("N.J.S.A. 54A:12" in c for c in r.pin_cites)
    assert any("P.L. 2021" in c for c in r.pin_cites)


def test_assumptions_cover_rate_schedule(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "NJ"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    text = " ".join(r.assumptions)
    assert "5.675%" in text or "10.9%" in text
