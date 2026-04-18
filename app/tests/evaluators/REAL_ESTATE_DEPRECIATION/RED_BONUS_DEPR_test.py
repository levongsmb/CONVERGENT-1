"""Tests for RED_BONUS_DEPR evaluator."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.evaluators._base import ConfigRulesAdapter
from app.evaluators.REAL_ESTATE_DEPRECIATION.RED_BONUS_DEPR import Evaluator
from app.scenario.loader import FIXTURES_DIR, load_scenario


@pytest.fixture
def rules():
    return ConfigRulesAdapter()


def _load(name):
    return load_scenario(FIXTURES_DIR / f"{name}.yaml")


def test_not_applicable_without_qualifying_property(rules):
    scenario = _load("scenario_single_1040")  # no assets except RSU lot
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is False


def test_real_property_current_year_defers_to_cost_seg(rules):
    """Real-estate fixture has commercial placed 2025-11. Not a 2026 acquisition
    → not_applicable under the strict year filter. Construct a 2026 acquisition."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_real_estate_investor.yaml").read_text()
    )
    # Move commercial placed_in_service to 2026
    for a in base["assets"]:
        if a["asset_code"] == "COMMERCIAL_C_BLDG":
            a["placed_in_service"] = "2026-02-15"
            a["acquisition_date"] = "2026-02-15"

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    assert result.computation_trace["defer_to_cost_seg"] is True


def test_applicable_for_equipment_purchase_in_planning_year(rules):
    """Construct a scenario with $200K equipment purchase in 2026."""
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["assets"].append({
        "asset_code": "EQ_LATHE_2026",
        "description": "CNC lathe acquired 2026 Q2",
        "asset_type": "EQUIPMENT",
        "placed_in_service": "2026-05-10",
        "acquisition_date": "2026-05-10",
        "cost_basis": 200000,
        "adjusted_basis": 200000,
    })

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert result.applicable is True
    trace = result.computation_trace
    assert trace["candidate_count"] == 1
    assert Decimal(trace["aggregate_basis"]) == Decimal("200000")
    assert Decimal(trace["first_year_bonus_deduction"]) == Decimal("200000")
    # 200000 * 32% = 64000
    assert result.estimated_tax_savings == Decimal("64000.00")


def test_multi_asset_aggregation(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["assets"].append({
        "asset_code": "EQ_A", "description": "Eq A",
        "asset_type": "EQUIPMENT", "placed_in_service": "2026-03-01",
        "cost_basis": 50000, "adjusted_basis": 50000,
    })
    base["assets"].append({
        "asset_code": "VEH_B", "description": "Veh B",
        "asset_type": "VEHICLE", "placed_in_service": "2026-04-01",
        "cost_basis": 80000, "adjusted_basis": 80000,
    })

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    trace = result.computation_trace
    assert trace["candidate_count"] == 2
    assert Decimal(trace["aggregate_basis"]) == Decimal("130000")


def test_cross_strategy_impacts(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["assets"].append({
        "asset_code": "EQ_A", "description": "Eq A",
        "asset_type": "EQUIPMENT", "placed_in_service": "2026-03-01",
        "cost_basis": 50000, "adjusted_basis": 50000,
    })

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert "RED_COST_SEG" in result.cross_strategy_impacts
    assert "RED_179" in result.cross_strategy_impacts
    assert "LL_461L" in result.cross_strategy_impacts
    assert "CA_NONCONFORMITY_BONUS" in result.cross_strategy_impacts


def test_pin_cites_include_168k_and_obbba(rules):
    import yaml

    base = yaml.safe_load(
        (FIXTURES_DIR / "scenario_mfj_scorp_owner.yaml").read_text()
    )
    base["assets"].append({
        "asset_code": "EQ_A", "description": "Eq A",
        "asset_type": "EQUIPMENT", "placed_in_service": "2026-03-01",
        "cost_basis": 50000, "adjusted_basis": 50000,
    })

    from app.scenario.models import ClientScenario

    scenario = ClientScenario.model_validate(base)
    result = Evaluator().evaluate(scenario, rules, year=2026)
    assert any("§168(k)" in c for c in result.pin_cites)
    assert any("OBBBA" in c for c in result.pin_cites)
    assert any("§280F" in c for c in result.pin_cites)
