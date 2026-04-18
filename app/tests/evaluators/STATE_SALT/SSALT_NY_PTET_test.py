"""Tests for SSALT_NY_PTET."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_NY_PTET import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_when_not_ny(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_when_ny_pte(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "NY"
    base["entities"][0]["operating_states"] = ["NY"]
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert r.applicable is True
    assert r.computation_trace["ny_pte_count"] == 1


def test_cross_strategy(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "NY"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert "SSALT_PTET_MODELING" in r.cross_strategy_impacts
    assert "SSALT_NYC_RESIDENT" in r.cross_strategy_impacts


def test_pin_cites_include_860_and_tsbm(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "NY"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert any("§§860-866" in c for c in r.pin_cites)
    assert any("TSB-M-21" in c for c in r.pin_cites)
    assert any("Notice 2020-75" in c for c in r.pin_cites)


def test_risks_flag_election_irrevocability(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "NY"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    text = " ".join(r.risks_and_caveats)
    assert "IRREVOCABLE" in text or "3/15" in text
