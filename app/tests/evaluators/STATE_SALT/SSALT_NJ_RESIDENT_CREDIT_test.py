"""Tests for SSALT_NJ_RESIDENT_CREDIT."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_NJ_RESIDENT_CREDIT import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_for_non_nj_resident(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_for_nj_resident(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_single_1040.yaml").read_text())
    base["identity"]["primary_state_domicile"] = "NJ"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_single_1040.yaml").read_text())
    base["identity"]["primary_state_domicile"] = "NJ"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert "SSALT_NJ_BAIT" in r.cross_strategy_impacts
    assert "SSALT_NY_PTET" in r.cross_strategy_impacts
    assert "SSALT_NY_CONVENIENCE_RULE" in r.cross_strategy_impacts


def test_pin_cites_include_54a_4_1_and_tannenbaum(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_single_1040.yaml").read_text())
    base["identity"]["primary_state_domicile"] = "NJ"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert any("54A:4-1" in c for c in r.pin_cites)
    assert any("Tannenbaum" in c for c in r.pin_cites)


def test_assumptions_cover_lesser_of_rule(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_single_1040.yaml").read_text())
    base["identity"]["primary_state_domicile"] = "NJ"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    text = " ".join(r.assumptions)
    assert "LOWER" in text or "lesser-of" in text.lower()
