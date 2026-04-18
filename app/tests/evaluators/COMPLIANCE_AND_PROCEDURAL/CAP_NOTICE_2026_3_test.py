"""Tests for CAP_NOTICE_2026_3."""
from __future__ import annotations
import pytest
from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.COMPLIANCE_AND_PROCEDURAL.CAP_NOTICE_2026_3 import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def test_not_applicable_without_farmland(rules):
    r = Evaluator().evaluate(load_scenario(FIXTURES_DIR / "scenario_single_1040.yaml"), rules, 2026)
    assert r.applicable is False


def test_applicable_on_farmland(rules):
    """Construct a scenario with a farmland asset."""
    import yaml
    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["assets"].append({
        "asset_code": "FARM_PARCEL",
        "description": "Agricultural land",
        "asset_type": "REAL_PROPERTY_FARMLAND",
        "acquisition_date": "2010-04-15",
        "cost_basis": 500000,
        "adjusted_basis": 500000,
    })
    from app.scenario.models import ClientScenario
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert r.applicable is True


def test_cross_strategy_includes_1062(rules):
    import yaml
    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["assets"].append({
        "asset_code": "FARM_PARCEL",
        "description": "Farmland",
        "asset_type": "REAL_PROPERTY_FARMLAND",
        "cost_basis": 400000, "adjusted_basis": 400000,
    })
    from app.scenario.models import ClientScenario
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert "FRA_1062_FARMLAND_INSTALL" in r.cross_strategy_impacts
    assert "FRA_NOTICE_2026_3" in r.cross_strategy_impacts


def test_pin_cites_include_notice_and_1062(rules):
    import yaml
    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["assets"].append({
        "asset_code": "FARM_PARCEL",
        "description": "Farmland",
        "asset_type": "REAL_PROPERTY_FARMLAND",
        "cost_basis": 400000, "adjusted_basis": 400000,
    })
    from app.scenario.models import ClientScenario
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    assert any("Notice 2026-3" in c for c in r.pin_cites)
    assert any("§1062" in c for c in r.pin_cites)
    assert any("§6654" in c for c in r.pin_cites)


def test_assumptions_cover_25_percent_factor(rules):
    import yaml
    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_single_1040.yaml").read_text()
    )
    base["assets"].append({
        "asset_code": "FARM_PARCEL",
        "description": "Farmland",
        "asset_type": "REAL_PROPERTY_FARMLAND",
        "cost_basis": 400000, "adjusted_basis": 400000,
    })
    from app.scenario.models import ClientScenario
    scenario = ClientScenario.model_validate(base)
    r = Evaluator().evaluate(scenario, rules, 2026)
    a = " ".join(r.assumptions)
    assert "25%" in a
