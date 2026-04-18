"""Tests for SSALT_CONFORMITY_DECOUPLING."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.STATE_SALT.SSALT_CONFORMITY_DECOUPLING import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_applicable_when_state_tax_exposure(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert r.applicable is True


def test_not_applicable_without_state_exposure(rules):
    import yaml
    from app.scenario.models import ClientScenario
    base = yaml.safe_load((FIXTURES_DIR / "scenario_single_1040.yaml").read_text())
    base["prior_year"]["total_state_tax_by_state"] = {}
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert r.applicable is False


def test_cross_strategy(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert "SSALT_NOL_CREDIT_CARRYFWD" in r.cross_strategy_impacts
    assert "ENT_QSBS_DRIVEN" in r.cross_strategy_impacts


def test_pin_cites_include_ca_17024_5(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    assert any("§17024.5" in c for c in r.pin_cites)
    assert any("§199A" in c for c in r.pin_cites)
    assert any("§168(k)" in c for c in r.pin_cites)


def test_assumptions_cover_ca_qbi_decoupling(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml"), rules, 2026)
    text = " ".join(r.assumptions)
    assert "bonus" in text.lower() or "168(k)" in text
    assert "199A" in text or "QBI" in text
