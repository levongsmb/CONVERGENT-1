"""RED_COST_SEG — cost segregation study opportunity.

A cost segregation engineer reclassifies components of a commercial
or residential rental property from 27.5- or 39-year MACRS into 5-, 7-,
and 15-year recovery periods, enabling bonus depreciation on the 5-,
7-, and 15-year components. Under OBBBA, §168(k) bonus is restored
to 100%, which revives the classical cost-seg play.

Applicability: taxpayer owns real property acquired within the last
4-5 years (Form 3115 §481(a) catch-up for older properties) with
cost basis above a typical study breakeven (~$750K).
"""

from __future__ import annotations

from decimal import Decimal
from typing import List

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import AssetType, ClientScenario


_STUDY_COST_FLOOR = Decimal("4000")  # firm-level minimum cost
_STUDY_COST_PCT_OF_BASIS = Decimal("0.005")  # 50 bps of basis
_BASIS_FLOOR = Decimal("750000")  # below this, study not usually cost-justified
_TYPICAL_RECLASSIFIED_PCT_COMMERCIAL = Decimal("0.25")  # 25% to 5/7/15 year
_TYPICAL_RECLASSIFIED_PCT_RESIDENTIAL = Decimal("0.15")  # 15% to 5/7/15 year


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "RED_COST_SEG"
    CATEGORY_CODE = "REAL_ESTATE_DEPRECIATION"
    PIN_CITES = [
        "IRC §168 — MACRS recovery periods",
        "IRC §168(k) as restored by OBBBA — 100% bonus depreciation",
        "Rev. Proc. 2015-13 / 2023-24 — automatic method changes",
        "IRS Chief Counsel Advice 201145016 — cost segregation methodology",
        "HCA, Inc. v. Commissioner, 109 T.C. 21 (1997) — cost-seg principles",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        candidates: List[tuple] = []
        for asset in scenario.assets:
            if asset.asset_type not in (
                AssetType.REAL_PROPERTY_COMMERCIAL,
                AssetType.REAL_PROPERTY_RESIDENTIAL,
            ):
                continue
            # Exclude personal residences without an explicit rental-use signal
            is_commercial = asset.asset_type == AssetType.REAL_PROPERTY_COMMERCIAL
            is_residential_rental = (
                asset.asset_type == AssetType.REAL_PROPERTY_RESIDENTIAL
                and "rental" in (asset.description or "").lower()
            )
            if not (is_commercial or is_residential_rental):
                continue
            if asset.cost_basis < _BASIS_FLOOR:
                continue
            # Age gate: placed in service within 5 years OR §481(a) catch-up
            if asset.placed_in_service is None:
                continue
            age = year - asset.placed_in_service.year
            candidates.append((asset, age, is_commercial))

        if not candidates:
            return self._not_applicable(
                "no commercial or rental real property asset with basis "
                f">= ${_BASIS_FLOOR:,.0f} and placed_in_service available"
            )

        total_first_year_acceleration = Decimal(0)
        per_asset: List[dict] = []
        for asset, age, is_commercial in candidates:
            reclass_pct = (
                _TYPICAL_RECLASSIFIED_PCT_COMMERCIAL
                if is_commercial
                else _TYPICAL_RECLASSIFIED_PCT_RESIDENTIAL
            )
            reclassified_basis = asset.cost_basis * reclass_pct
            # 100% bonus on the reclassified components in the first cost-seg year
            first_year_depreciation = reclassified_basis
            # Subtract what would have been taken under straight MACRS in year 1
            baseline_lives = Decimal("39") if is_commercial else Decimal("27.5")
            baseline_year_1 = (asset.cost_basis / baseline_lives / Decimal("2"))  # mid-month prorate approximation
            # Acceleration = bonus - what would have been taken on the reclassified component on straight MACRS
            baseline_on_reclassified = reclassified_basis / baseline_lives / Decimal("2")
            acceleration = (first_year_depreciation - baseline_on_reclassified).quantize(Decimal("0.01"))
            total_first_year_acceleration += acceleration

            study_cost = max(
                _STUDY_COST_FLOOR,
                (asset.cost_basis * _STUDY_COST_PCT_OF_BASIS).quantize(Decimal("0.01")),
            )
            per_asset.append({
                "asset_code": asset.asset_code,
                "cost_basis": str(asset.cost_basis),
                "age_years": age,
                "is_commercial": is_commercial,
                "reclassified_pct": str(reclass_pct),
                "reclassified_basis": str(reclassified_basis),
                "first_year_acceleration": str(acceleration),
                "estimated_study_cost": str(study_cost),
            })

        approx_marginal = Decimal("0.32")
        estimated_fed_save = (total_first_year_acceleration * approx_marginal).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=estimated_fed_save,
            savings_by_tax_type=TaxImpact(federal_income_tax=estimated_fed_save),
            inputs_required=[
                "engineering cost segregation study per property",
                "construction cost breakdown if available (components, useful lives)",
                "§469 passive / material participation posture (pairs with LL_469_PASSIVE and LL_REP_STATUS)",
                "§168(g)(1)(A) ADS election-out posture for §163(j)(7)(B) electing entities",
                "state conformity posture (CA does not conform to §168(k))",
            ],
            assumptions=[
                f"Typical reclassified pct (commercial): {_TYPICAL_RECLASSIFIED_PCT_COMMERCIAL:.0%}",
                f"Typical reclassified pct (residential): {_TYPICAL_RECLASSIFIED_PCT_RESIDENTIAL:.0%}",
                f"Approx marginal rate: {approx_marginal:.0%}",
                f"Total first-year acceleration estimated: ${total_first_year_acceleration:,.2f}",
                f"§168(k) bonus depreciation under OBBBA: 100%",
                "Recapture at ordinary rates on sale (up to 25% for §1250 unrecaptured).",
            ],
            implementation_steps=[
                "Commission the cost segregation engineer (typical cost "
                "$4K-$20K or 50 bps of basis for large properties).",
                "File Form 3115 for §481(a) catch-up if property has been in "
                "service > 1 year; otherwise claim via Form 4562 on the "
                "current-year return.",
                "Pair with §469 passive-loss analysis: the first-year "
                "acceleration generates suspended losses unless the taxpayer "
                "qualifies for REP status (LL_REP_STATUS) or the STR "
                "exception (LL_STR_EXCEPTION).",
                "Track the reclassified components in the fixed-asset ledger "
                "separately for state nonconformity (CA) and for recapture "
                "computation on sale.",
            ],
            risks_and_caveats=[
                "§163(j)(7)(B) electing real-property-trade entities MUST use "
                "ADS depreciation; cost seg components are depreciated under "
                "ADS lives, substantially reducing the benefit.",
                "Recapture on sale: §1245 ordinary recapture on 5/7/15-year "
                "components; §1250 unrecaptured gain at 25% on the real-"
                "property shell. Cost-seg accelerates deduction timing but "
                "does not reduce total tax over the life of the asset.",
                "CA does not conform to §168(k) bonus; California basis "
                "remains at MACRS straight-line. Track state nonconformity "
                "basis (Asset.state_nonconformity_basis).",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "RED_BONUS_DEPR",
                "RED_163J_REPTOB",
                "RED_PARTIAL_DISP",
                "RED_STR_CLASSIF",
                "RED_RECAPTURE_PLAN",
                "LL_REP_STATUS",
                "LL_469_PASSIVE",
                "CA_NONCONFORMITY_BONUS",
            ],
            verification_confidence="medium",
            computation_trace={
                "candidate_count": len(candidates),
                "total_first_year_acceleration": str(total_first_year_acceleration),
                "approx_marginal_rate": str(approx_marginal),
                "per_asset": per_asset,
            },
        )
