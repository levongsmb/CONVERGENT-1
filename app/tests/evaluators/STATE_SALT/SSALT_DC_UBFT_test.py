"""Tests for SSALT_DC_UBFT."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_DC_UBFT import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_dc_unincorporated(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_with_dc_llc(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_partnership_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "DC"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert r.applicable is True


def test_cross_strategy(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_partnership_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "DC"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert "SSALT_DC_SERVICE_SOURCING" in r.cross_strategy_impacts
    assert "SSALT_PTET_MODELING" in r.cross_strategy_impacts


def test_pin_cites_include_ubft_statute(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_partnership_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "DC"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert any("§47-1808.01" in c for c in r.pin_cites)
    assert any("§47-1808.03" in c for c in r.pin_cites)


def test_assumptions_cover_8_25_rate_and_80_pct(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_partnership_owner.yaml").read_text())
    base["entities"][0]["formation_state"] = "DC"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    text = " ".join(r.assumptions)
    assert "8.25%" in text
    assert "80%" in text
