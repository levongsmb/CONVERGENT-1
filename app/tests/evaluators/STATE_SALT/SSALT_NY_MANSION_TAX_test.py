"""Tests for SSALT_NY_MANSION_TAX."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_NY_MANSION_TAX import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_ny_residential(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_with_ny_residential(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["assets"][0]["location_state"] = "NY"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["assets"][0]["location_state"] = "NY"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert "SSALT_TRANSFER_TAX" in r.cross_strategy_impacts
    assert "EST_GIFT_VALUATION" in r.cross_strategy_impacts


def test_pin_cites_include_1402_and_1402a(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["assets"][0]["location_state"] = "NY"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert any("§1402-a" in c for c in r.pin_cites)
    assert any("§11-2101" in c for c in r.pin_cites)


def test_assumptions_cover_1_percent_threshold(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["assets"][0]["location_state"] = "NY"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    text = " ".join(r.assumptions)
    assert "1%" in text and "$1M" in text
