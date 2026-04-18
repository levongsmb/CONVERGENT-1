"""CGL_GAIN_BUNCHING — timing flexibility on gain realization.

When a taxpayer has flexibility on WHEN to realize long-term capital
gains (appreciated stock held with no immediate liquidity need), the
strategy is to land those gains in years with the lowest marginal
§1(h) rate. The 0% LTCG bracket applies up to the §1(h) threshold,
15% between thresholds, 20% above — with the 3.8% NIIT stacking at
the MAGI threshold.

Applicable when scenario has appreciated securities that could be sold
this year or next.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import AssetType, ClientScenario, FilingStatus


_TAXABLE_TYPES = {AssetType.STOCK_PUBLIC, AssetType.STOCK_PRIVATE, AssetType.CRYPTO}


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CGL_GAIN_BUNCHING"
    CATEGORY_CODE = "CAPITAL_GAINS_LOSSES"
    PIN_CITES = [
        "IRC §1(h) — capital gains rate structure (0/15/20%)",
        "IRC §1(h)(1)(B) — 0% bracket up to §1(h) threshold",
        "IRC §1411 — NIIT 3.8% at MAGI threshold",
        "IRC §1223 — holding period rules",
        "Rev. Proc. 2025-32 — 2026 §1(h) bracket breakpoints",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        taxable_lots = [
            a for a in scenario.assets
            if a.asset_type in _TAXABLE_TYPES
            and a.fmv is not None
            and a.adjusted_basis is not None
        ]
        unrealized_gains: List[dict] = []
        total_unrealized_gain = Decimal(0)
        for lot in taxable_lots:
            delta = lot.fmv - lot.adjusted_basis
            if delta > Decimal(0):
                unrealized_gains.append({
                    "asset_code": lot.asset_code,
                    "description": lot.description,
                    "basis": str(lot.adjusted_basis),
                    "fmv": str(lot.fmv),
                    "gain": str(delta),
                })
                total_unrealized_gain += delta

        if total_unrealized_gain <= Decimal(0):
            return self._not_applicable(
                "no unrealized gains in taxable securities; bunching requires "
                "appreciated positions"
            )

        # Current realized gains
        realized_lt = scenario.income.capital_gains_long_term
        realized_st = scenario.income.capital_gains_short_term

        # §1(h) breakpoints for year: awaiting in rules cache;
        # surface awaiting-cache posture gracefully if null
        cg = rules.get("federal/capital_gain_brackets", year)
        filing_status = scenario.identity.filing_status
        fs_key = "MFJ" if filing_status == FilingStatus.MFJ else (
            "MFS" if filing_status == FilingStatus.MFS else "SINGLE"
        )
        breakpoint_0_to_15 = None
        breakpoint_15_to_20 = None
        for p in cg.get("parameters", []):
            c = p["coordinate"]
            sp = c.get("sub_parameter")
            fs = c.get("filing_status")
            v = p.get("value")
            if v is None or fs != fs_key:
                continue
            if sp == "breakpoint_0_to_15":
                breakpoint_0_to_15 = Decimal(str(v))
            elif sp == "breakpoint_15_to_20":
                breakpoint_15_to_20 = Decimal(str(v))

        assumptions: List[str] = [
            f"Filing status: {fs_key}",
            f"Unrealized LT gain candidates: ${total_unrealized_gain:,.2f}",
            f"Current-year realized LT gain: ${realized_lt:,.2f}",
            f"Current-year realized ST gain: ${realized_st:,.2f}",
        ]
        if breakpoint_0_to_15 is None or breakpoint_15_to_20 is None:
            assumptions.append(
                "§1(h) bracket breakpoints for planning year are awaiting "
                "Rev. Proc. population; timing windows cannot be quantified."
            )
            confidence = "low"
        else:
            assumptions.append(
                f"0% / 15% breakpoint: ${breakpoint_0_to_15:,.0f}"
            )
            assumptions.append(
                f"15% / 20% breakpoint: ${breakpoint_15_to_20:,.0f}"
            )
            confidence = "high"

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),  # path-dependent on projected income
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "projected taxable income per planning year over 3-5 year window",
                "expected realized LT gain each year (baseline)",
                "§1(h) bracket breakpoints for each planning year",
                "MAGI posture at §1411 NIIT threshold",
                "state of residence at realization year (CA taxes LT at ordinary)",
            ],
            assumptions=assumptions,
            implementation_steps=[
                "Model 3-5 year taxable-income path; identify low-income years "
                "(sabbatical, retirement bridge, loss year).",
                "For each candidate lot, select the realization year that "
                "lands the entire gain inside the 0% or 15% bracket given the "
                "year's other income.",
                "Coordinate with CGL_TAX_LOSS_HARVEST for paired gain/loss "
                "realizations that net to zero.",
                "For MFJ above $250K MAGI, each dollar of LT gain also triggers "
                "3.8% NIIT; consider splitting the realization across tax "
                "years to stay below threshold.",
            ],
            risks_and_caveats=[
                "State tax: CA, HI, MN, NJ, OR (and others) tax LT gain at "
                "ordinary rates. Bunching into a zero-federal-rate year still "
                "costs state tax at the resident rate.",
                "Collectibles gain under §1(h)(4) is capped at 28%; §1202 "
                "non-excluded gain also at 28%. Bunching analysis must "
                "classify gain type correctly.",
                "AMT interaction: large LT gain in a single year can trigger "
                "AMT exposure via the AMT preference items on Schedule 6251.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "CGL_TAX_LOSS_HARVEST",
                "CGL_CARRYFORWARDS",
                "CGL_NETTING",
                "CGL_NIIT_INTERACT",
                "NIIT_CAP_GAIN_HARVEST",
                "RET_ROTH_CONVERSION",
                "RD_CA_DOMICILE_BREAK",
            ],
            verification_confidence=confidence,
            computation_trace={
                "unrealized_gains": unrealized_gains,
                "total_unrealized_gain": str(total_unrealized_gain),
                "realized_lt_gain_current": str(realized_lt),
                "realized_st_gain_current": str(realized_st),
                "breakpoint_0_to_15": str(breakpoint_0_to_15) if breakpoint_0_to_15 else None,
                "breakpoint_15_to_20": str(breakpoint_15_to_20) if breakpoint_15_to_20 else None,
                "filing_status": fs_key,
            },
        )
