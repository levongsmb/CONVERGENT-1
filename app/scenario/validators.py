"""Cross-scenario consistency checks.

Model-level validators in `app.scenario.models` enforce two invariants
(K-1 references an entity in the entities list; filing status agrees with
spouse presence). This module adds deeper cross-field checks that read the
scenario holistically. They return a list of diagnostic strings. An empty
list means the scenario is clean.

Callers should run `validate_scenario(scenario)` after Pydantic construction
and treat any returned diagnostic as a blocking issue unless explicitly
documented as informational in the fixture.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List

from app.scenario.models import (
    AssetType,
    ClientScenario,
    EntityType,
    FilingStatus,
    StateCode,
)


def validate_scenario(scenario: ClientScenario) -> List[str]:
    issues: List[str] = []
    issues.extend(_validate_entity_ownership_bounds(scenario))
    issues.extend(_validate_qsbs_asset_metadata(scenario))
    issues.extend(_validate_scorp_basis_presence(scenario))
    issues.extend(_validate_partnership_outside_basis_presence(scenario))
    issues.extend(_validate_planning_liquidity_event_shape(scenario))
    issues.extend(_validate_state_sourcing_coverage(scenario))
    issues.extend(_validate_dependents_shape(scenario))
    issues.extend(_validate_community_property_flag_state(scenario))
    return issues


def _validate_entity_ownership_bounds(scenario: ClientScenario) -> List[str]:
    out: List[str] = []
    for e in scenario.entities:
        if e.ownership_pct_by_taxpayer < Decimal(0) or e.ownership_pct_by_taxpayer > Decimal(100):
            out.append(
                f"entity {e.code}: ownership_pct_by_taxpayer {e.ownership_pct_by_taxpayer} "
                f"is outside [0, 100]"
            )
    return out


def _validate_qsbs_asset_metadata(scenario: ClientScenario) -> List[str]:
    out: List[str] = []
    for asset in scenario.assets:
        if asset.asset_type == AssetType.STOCK_QSBS or asset.is_qsbs:
            if asset.qsbs_issuance_date is None:
                out.append(
                    f"asset {asset.asset_code}: QSBS flagged but qsbs_issuance_date is missing; "
                    f"holding-period tiering cannot be computed"
                )
            if asset.qsbs_pre_or_post_obbba is None:
                out.append(
                    f"asset {asset.asset_code}: QSBS flagged but qsbs_pre_or_post_obbba is missing; "
                    f"exclusion rule set ambiguous"
                )
            if asset.qsbs_issuer_ein is None:
                out.append(
                    f"asset {asset.asset_code}: QSBS flagged but qsbs_issuer_ein is missing; "
                    f"per-issuer cap aggregation cannot be computed"
                )
    return out


def _validate_scorp_basis_presence(scenario: ClientScenario) -> List[str]:
    out: List[str] = []
    for e in scenario.entities:
        if e.type in (EntityType.S_CORP, EntityType.LLC_S_CORP):
            if e.stock_basis is None:
                out.append(
                    f"entity {e.code}: S corp without stock_basis; §1366(d) loss limitation "
                    f"computations will be blocked"
                )
    return out


def _validate_partnership_outside_basis_presence(scenario: ClientScenario) -> List[str]:
    out: List[str] = []
    for e in scenario.entities:
        if e.type in (EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP):
            if e.outside_basis is None:
                out.append(
                    f"entity {e.code}: partnership without outside_basis; §704(d) limitation "
                    f"computations will be blocked"
                )
    return out


def _validate_planning_liquidity_event_shape(scenario: ClientScenario) -> List[str]:
    out: List[str] = []
    planned = scenario.planning.liquidity_event_planned
    if planned is not None:
        if "target_close_date" not in planned:
            out.append("planning.liquidity_event_planned is set but lacks target_close_date")
        if "expected_proceeds" not in planned:
            out.append("planning.liquidity_event_planned is set but lacks expected_proceeds")
    if "LIQUIDITY_EVENT_PREP" in scenario.planning.objectives and planned is None:
        out.append(
            "planning objectives include LIQUIDITY_EVENT_PREP but liquidity_event_planned is None"
        )
    return out


def _validate_state_sourcing_coverage(scenario: ClientScenario) -> List[str]:
    """When a taxpayer is part-year or has income sourced to a nonresident state,
    any other_income entry declaring state_sourcing must include the resident
    state among its keys so non-resident credit computations balance.
    """
    out: List[str] = []
    resident_state = scenario.identity.primary_state_domicile
    for item in scenario.income.other_income:
        if item.state_sourcing is not None and len(item.state_sourcing) > 1:
            if resident_state not in item.state_sourcing:
                out.append(
                    f"other_income '{item.income_type}' has multi-state sourcing but omits "
                    f"resident state {resident_state.value}; resident-credit math will be off"
                )
    return out


def _validate_dependents_shape(scenario: ClientScenario) -> List[str]:
    out: List[str] = []
    required_keys = {"relationship", "dob"}
    for i, dep in enumerate(scenario.identity.dependents):
        missing = required_keys - set(dep.keys())
        if missing:
            out.append(f"dependents[{i}] missing required keys: {sorted(missing)}")
    return out


_COMMUNITY_PROPERTY_STATES = {
    StateCode.AZ, StateCode.CA, StateCode.ID, StateCode.LA, StateCode.NV,
    StateCode.NM, StateCode.TX, StateCode.WA, StateCode.WI,
}


def _validate_community_property_flag_state(scenario: ClientScenario) -> List[str]:
    """Informational: when MFJ/MFS and both spouses domicile in a community
    property state, surface a reminder so evaluators that split income by
    spouse honor the state law default.
    """
    out: List[str] = []
    if scenario.identity.filing_status not in (FilingStatus.MFJ, FilingStatus.MFS):
        return out
    if scenario.identity.spouse_state_domicile is None:
        return out
    primary_cp = scenario.identity.primary_state_domicile in _COMMUNITY_PROPERTY_STATES
    spouse_cp = scenario.identity.spouse_state_domicile in _COMMUNITY_PROPERTY_STATES
    if primary_cp and spouse_cp and scenario.identity.filing_status == FilingStatus.MFS:
        out.append(
            f"INFO: both spouses domicile in community property states "
            f"(primary={scenario.identity.primary_state_domicile.value}, "
            f"spouse={scenario.identity.spouse_state_domicile.value}) and filing MFS; "
            f"evaluators must split community-property income per state law"
        )
    return out
