"""Tests for SSALT_164_SALT_CAP."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_164_SALT_CAP import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable_when_salt_paid(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_not_applicable_when_no_salt(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_single_1040.yaml").read_text())
    base["deductions"]["salt_paid_state_income"] = 0
    base["deductions"]["salt_paid_property_personal"] = 0
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert r.applicable is False


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "SSALT_OBBBA_CAP_MODELING" in r.cross_strategy_impacts
    assert "SSALT_PTET_MODELING" in r.cross_strategy_impacts
    assert "CHAR_OBBBA_37_CAP" in r.cross_strategy_impacts


def test_pin_cites(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("§164(a)" in c for c in r.pin_cites)
    assert any("§164(b)(6)" in c for c in r.pin_cites)
    assert any("Notice 2020-75" in c for c in r.pin_cites)


def test_assumptions_flag_investment_property_exception(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    text = " ".join(r.assumptions)
    assert "investment" in text.lower() or "Schedule E" in text
