"""RED_BONUS_DEPR — §168(k) bonus depreciation under OBBBA.

OBBBA restored §168(k) 100% bonus depreciation on qualified property
placed in service after 2025-01-19. Applicable to any scenario with
recent qualified property purchases: equipment, vehicles (with
§280F limits), QIP, and the 5/7/15-year components from cost seg.

This evaluator identifies candidate assets placed in the planning year
and flags the bonus-depreciation election vs §179 vs straight-line
tradeoffs. Coordinates with RED_COST_SEG for the reclassification leg.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import AssetType, ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "RED_BONUS_DEPR"
    CATEGORY_CODE = "REAL_ESTATE_DEPRECIATION"
    PIN_CITES = [
        "IRC §168(k) as restored by OBBBA — 100% bonus for property placed in "
        "service after 2025-01-19",
        "IRC §168(k)(2)(A) — qualified property definition",
        "IRC §280F — luxury auto limitation",
        "IRC §168(g) — ADS election-out",
        "Rev. Proc. 2020-25 / 2023-24 — automatic method change procedures",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        # Applicable asset types for bonus: non-real-property generally, plus
        # QIP (§168(e)(6)) and 5/7/15-year property.
        eligible_types = {
            AssetType.EQUIPMENT,
            AssetType.VEHICLE,
            AssetType.INTANGIBLE,  # limited — only certain §197 intangibles
        }
        candidates = [
            a for a in scenario.assets
            if a.asset_type in eligible_types
            and a.placed_in_service is not None
            and a.placed_in_service.year == year
        ]
        if not candidates:
            # Also accept real-property assets for the cost-seg handoff case
            real_candidates = [
                a for a in scenario.assets
                if a.asset_type in (
                    AssetType.REAL_PROPERTY_COMMERCIAL,
                    AssetType.REAL_PROPERTY_RESIDENTIAL,
                )
                and a.placed_in_service is not None
                and a.placed_in_service.year == year
            ]
            if not real_candidates:
                return self._not_applicable(
                    f"no qualified property placed in service in {year}; "
                    f"§168(k) bonus applies to current-year acquisitions"
                )
            # Defer the main bonus opportunity to cost seg
            return StrategyResult(
                subcategory_code=self.SUBCATEGORY_CODE,
                applicable=True,
                reason="current-year acquisition is real property; primary "
                       "bonus opportunity is via cost segregation reclassification",
                pin_cites=list(self.PIN_CITES),
                verification_confidence="high",
                cross_strategy_impacts=[
                    "RED_COST_SEG",
                    "RED_PARTIAL_DISP",
                    "CA_NONCONFORMITY_BONUS",
                ],
                computation_trace={
                    "current_year_real_property_count": len(real_candidates),
                    "defer_to_cost_seg": True,
                },
            )

        total_basis = sum((a.cost_basis for a in candidates), start=Decimal(0))
        total_bonus_first_year = total_basis  # 100% bonus
        approx_marginal = Decimal("0.32")
        estimated_fed_save = (total_bonus_first_year * approx_marginal).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=estimated_fed_save,
            savings_by_tax_type=TaxImpact(federal_income_tax=estimated_fed_save),
            inputs_required=[
                "acquisition date and cost for each planning-year purchase",
                "§280F luxury-auto facts for any vehicle placed in service",
                "§168(g) ADS election-out decisions per entity",
                "state nonconformity posture (CA does not conform to §168(k))",
            ],
            assumptions=[
                f"Planning year: {year}",
                f"Candidate qualified-property assets: {len(candidates)}",
                f"Aggregate basis: ${total_basis:,.2f}",
                f"100% bonus first-year deduction: ${total_bonus_first_year:,.2f}",
                f"Approx marginal rate: {approx_marginal:.0%}",
            ],
            implementation_steps=[
                "Confirm each asset is §168(k)(2)(A) qualified property (new "
                "or used, original use with the taxpayer for acquired-used "
                "property under §168(k)(2)(E)(ii)).",
                "Evaluate the §168(k)(7) election-out on an asset-class basis "
                "if spreading depreciation across years is preferred.",
                "Coordinate §280F limits on vehicles; luxury-auto cap may "
                "restrict first-year deduction even with bonus.",
                "For each §163(j)(7)(B) real-property-trade entity, confirm "
                "ADS is applied (bonus does not apply to ADS-depreciated "
                "property).",
                "Track state nonconformity basis for CA (and any other "
                "non-conforming state).",
            ],
            risks_and_caveats=[
                "OBBBA restored 100% bonus for property placed in service "
                "AFTER 2025-01-19. Property placed in service between "
                "2025-01-01 and 2025-01-19 may fall under pre-OBBBA phase-down "
                "rules; confirm acquisition date.",
                "CA does not conform to §168(k) — state basis remains at "
                "MACRS straight-line; maintain parallel CA depreciation "
                "schedules.",
                "Bonus timing choice interacts with §461(l) excess business "
                "loss, §469 passive, and §163(j) ATI. A large first-year "
                "bonus may be partially disallowed and deferred.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "RED_COST_SEG",
                "RED_179",
                "RED_163J_REPTOB",
                "RED_PARTIAL_DISP",
                "LL_461L",
                "LL_469_PASSIVE",
                "LL_163J_INTEREST",
                "CA_NONCONFORMITY_BONUS",
            ],
            verification_confidence="high",
            computation_trace={
                "candidate_count": len(candidates),
                "aggregate_basis": str(total_basis),
                "first_year_bonus_deduction": str(total_bonus_first_year),
                "approx_marginal_rate": str(approx_marginal),
                "candidate_assets": [
                    {"code": a.asset_code, "basis": str(a.cost_basis), "type": a.asset_type.value}
                    for a in candidates
                ],
            },
        )
