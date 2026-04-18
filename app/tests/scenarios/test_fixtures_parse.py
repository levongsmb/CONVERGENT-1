"""Phase 1a acceptance tests — every fixture parses cleanly through
ClientScenario and emerges with no blocking validator diagnostics.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from app.scenario.loader import fixture_paths, load_scenario
from app.scenario.models import ClientScenario, EntityType, FilingStatus
from app.scenario.validators import validate_scenario


FIXTURE_IDS = [
    "scenario_single_1040",
    "scenario_mfj_scorp_owner",
    "scenario_partnership_owner",
    "scenario_real_estate_investor",
    "scenario_qsbs_founder",
    "scenario_trust_beneficiary",
    "scenario_liquidity_event",
]


def _fixture_for(name: str) -> Path:
    for p in fixture_paths():
        if p.stem == name:
            return p
    raise FileNotFoundError(f"fixture {name} not found under app/scenario/fixtures/")


@pytest.mark.parametrize("fixture_name", FIXTURE_IDS)
def test_fixture_parses(fixture_name: str):
    scenario = load_scenario(_fixture_for(fixture_name))
    assert isinstance(scenario, ClientScenario)
    assert scenario.scenario_id
    assert scenario.identity.tax_year >= 2026


@pytest.mark.parametrize("fixture_name", FIXTURE_IDS)
def test_fixture_no_blocking_validator_issues(fixture_name: str):
    scenario = load_scenario(_fixture_for(fixture_name))
    diagnostics = validate_scenario(scenario)
    blocking = [d for d in diagnostics if not d.startswith("INFO:")]
    assert blocking == [], f"{fixture_name} produced blocking diagnostics: {blocking}"


def test_all_fixtures_present():
    """Seven fixtures required by spec Section 2.3."""
    stems = {p.stem for p in fixture_paths()}
    assert stems == set(FIXTURE_IDS), f"fixture set mismatch: {stems ^ set(FIXTURE_IDS)}"


def test_scorp_owner_has_qbi_components():
    scenario = load_scenario(_fixture_for("scenario_mfj_scorp_owner"))
    scorp_k1s = [k for k in scenario.income.k1_income if k.entity_type == EntityType.S_CORP]
    assert len(scorp_k1s) == 1
    k1 = scorp_k1s[0]
    assert k1.qualified_business_income > Decimal(0)
    assert k1.w2_wages_allocated > Decimal(0)
    assert k1.ubia_allocated > Decimal(0)


def test_qsbs_founder_has_pre_and_post_obbba_lots():
    scenario = load_scenario(_fixture_for("scenario_qsbs_founder"))
    qsbs_lots = [a for a in scenario.assets if a.is_qsbs]
    assert len(qsbs_lots) == 2
    tiers = {a.qsbs_pre_or_post_obbba for a in qsbs_lots}
    assert tiers == {"PRE", "POST"}


def test_liquidity_event_has_planned_block():
    scenario = load_scenario(_fixture_for("scenario_liquidity_event"))
    assert scenario.planning.liquidity_event_planned is not None
    assert "target_close_date" in scenario.planning.liquidity_event_planned
    assert "expected_proceeds" in scenario.planning.liquidity_event_planned


def test_k1_orphan_raises():
    """The model-level validator rejects a K-1 that references an unknown entity code."""
    import yaml

    base = yaml.safe_load(_fixture_for("scenario_single_1040").read_text())
    base["income"]["k1_income"] = [{
        "entity_code": "DOES_NOT_EXIST",
        "entity_type": "S_CORP",
        "ownership_pct": 10,
    }]
    with pytest.raises(Exception) as exc_info:
        ClientScenario.model_validate(base)
    assert "DOES_NOT_EXIST" in str(exc_info.value)


def test_mfj_without_spouse_dob_raises():
    import yaml

    base = yaml.safe_load(_fixture_for("scenario_single_1040").read_text())
    base["identity"]["filing_status"] = "MFJ"
    # spouse_dob deliberately omitted
    with pytest.raises(Exception) as exc_info:
        ClientScenario.model_validate(base)
    assert "spouse_dob" in str(exc_info.value)


def test_single_with_spouse_dob_raises():
    import yaml

    base = yaml.safe_load(_fixture_for("scenario_mfj_scorp_owner").read_text())
    base["identity"]["filing_status"] = "SINGLE"
    # keep spouse_dob to trigger the inverse invariant
    with pytest.raises(Exception) as exc_info:
        ClientScenario.model_validate(base)
    assert "SINGLE" in str(exc_info.value) or "spouse_dob" in str(exc_info.value)


def test_decimal_precision_preserved_through_yaml():
    """Dollar amounts round-trip through YAML as Decimal, not float."""
    scenario = load_scenario(_fixture_for("scenario_liquidity_event"))
    # Identity test value known exactly
    stock_basis = scenario.entities[0].stock_basis
    assert stock_basis == Decimal("1850000")
    # Confirm type
    assert isinstance(stock_basis, Decimal)
    k1 = scenario.income.k1_income[0]
    assert isinstance(k1.ordinary_business_income, Decimal)
    assert k1.ordinary_business_income == Decimal("1420000")
