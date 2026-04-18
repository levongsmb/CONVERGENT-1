"""Tests for SSALT_NY_INVESTMENT_CAPITAL."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_NY_INVESTMENT_CAPITAL import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_for_ca_corp(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_for_ny_corp(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "NY"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "NY"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert "SSALT_CONFORMITY_DECOUPLING" in r.cross_strategy_impacts
    assert "SSALT_NY_PTET" in r.cross_strategy_impacts


def test_pin_cites_include_208_and_tsbm(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "NY"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert any("§208.5" in c for c in r.pin_cites)
    assert any("TSB-M-15(8)C" in c for c in r.pin_cites)


def test_assumptions_cover_1_year_tag(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "NY"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    text = " ".join(r.assumptions)
    assert "1 year" in text or "one year" in text.lower() or "within" in text.lower()
