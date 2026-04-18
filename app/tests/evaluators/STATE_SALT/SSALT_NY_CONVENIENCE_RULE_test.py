"""Tests for SSALT_NY_CONVENIENCE_RULE."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_NY_CONVENIENCE_RULE import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_wages(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text())
    base["income"]["wages_primary"] = 0
    base["income"]["wages_spouse"] = 0
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert r.applicable is False


def test_not_applicable_for_ny_resident(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_single_1040.yaml").read_text())
    base["identity"]["primary_state_domicile"] = "NY"
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert r.applicable is False


def test_applicable_for_non_ny_wage_earner(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_pin_cites_include_zelinsky_and_132_18(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("§132.18(a)" in c for c in r.pin_cites)
    assert any("Zelinsky" in c for c in r.pin_cites)
    assert any("Huckaby" in c for c in r.pin_cites)


def test_risks_flag_double_tax_from_ct(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    text = " ".join(r.risks_and_caveats)
    assert "Connecticut" in text or "CT" in text
