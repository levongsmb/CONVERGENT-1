"""QSBS_HOLDING_PERIOD — track holding period and qualifying exclusion tier.

Pre-OBBBA QSBS (issued on or before 2025-07-04): strict 5-year hold for
100% exclusion — no partial tiers.

Post-OBBBA QSBS (issued after 2025-07-04) under §1202(a) as amended by
OBBBA §70431:
  - 50% exclusion at >= 3-year hold
  - 75% exclusion at >= 4-year hold
  - 100% exclusion at >= 5-year hold

This evaluator computes the current holding period for each QSBS lot
and identifies the earliest exclusion-tier window and the date at which
the next tier vests. Coordinates with QSBS_OBBBA_TIERED for the dollar
exclusion math.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import date, timedelta

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


_OBBBA_EFFECTIVE_DATE = date(2025, 7, 4)


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "QSBS_HOLDING_PERIOD"
    CATEGORY_CODE = "QSBS_1202"
    PIN_CITES = [
        "IRC §1202(a)(1) — 100% exclusion at 5-year hold",
        "IRC §1202(a) as amended by OBBBA — 50% (3y) / 75% (4y) / 100% (5y) tiers",
        "IRC §1202(h)(1) — holding period tacking for gifts and reorganizations",
        "P.L. 119-21 §70431 — OBBBA §1202 amendments effective 2025-07-04",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        qsbs_lots = [a for a in scenario.assets if a.is_qsbs and a.qsbs_issuance_date is not None]
        if not qsbs_lots:
            return self._not_applicable(
                "no QSBS-flagged assets with issuance_date in scenario"
            )

        # Reference date: end of planning year (for holding-period computation)
        ref_date = date(year, 12, 31)
        lot_details: list = []
        for a in qsbs_lots:
            issuance = a.qsbs_issuance_date
            regime = (
                a.qsbs_pre_or_post_obbba
                or ("POST" if issuance > _OBBBA_EFFECTIVE_DATE else "PRE")
            )
            days_held = (ref_date - issuance).days
            years_held = days_held / 365.25

            if regime == "PRE":
                current_exclusion_pct = Decimal("1.00") if years_held >= 5 else Decimal("0.00")
                next_tier_date = (
                    issuance + timedelta(days=int(5 * 365.25))
                    if years_held < 5 else None
                )
                tiers = [("5y", 5, Decimal("1.00"))]
            else:
                tiers = [
                    ("3y", 3, Decimal("0.50")),
                    ("4y", 4, Decimal("0.75")),
                    ("5y", 5, Decimal("1.00")),
                ]
                current_exclusion_pct = Decimal("0.00")
                next_tier_date = None
                for _label, yrs, pct in tiers:
                    if years_held >= yrs:
                        current_exclusion_pct = pct
                    elif next_tier_date is None:
                        next_tier_date = issuance + timedelta(days=int(yrs * 365.25))

            unrealized = (a.fmv - a.adjusted_basis) if a.fmv is not None else None
            lot_details.append({
                "asset_code": a.asset_code,
                "issuance_date": str(issuance),
                "regime": regime,
                "days_held_as_of_year_end": days_held,
                "years_held": f"{years_held:.2f}",
                "current_exclusion_pct": str(current_exclusion_pct),
                "next_tier_vest_date": str(next_tier_date) if next_tier_date else None,
                "unrealized_gain": str(unrealized) if unrealized is not None else None,
            })

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "issuance date and regime (pre/post-OBBBA) per lot",
                "acquisition date and tacking history (for §1202(h) carryover)",
                "liquidity-event target date (compare against next_tier_vest_date)",
                "FMV at planned sale date",
            ],
            assumptions=[
                f"Reference date (end of planning year): {ref_date}",
                f"OBBBA effective date: {_OBBBA_EFFECTIVE_DATE}",
                f"QSBS lots tracked: {len(qsbs_lots)}",
            ],
            implementation_steps=[
                "For each lot, annotate the next_tier_vest_date on the tax "
                "workpaper and coordinate with the liquidity-event target.",
                "If a lot is approaching a tier boundary near a planned sale, "
                "consider a §1045 rollover (cross-reference QSBS_1045_ROLLOVER) "
                "to defer realization until the next tier vests.",
                "For §1202(h) tacked stock (gifted or §351-received), document "
                "the prior owner's holding period in the permanent file.",
                "If the taxpayer has both pre- and post-OBBBA lots, track them "
                "in separate schedules — different exclusion rules and per-"
                "issuer cap amounts apply.",
            ],
            risks_and_caveats=[
                "Holding period counting: §1202 holding period starts the day "
                "after the issuance date (§1(h), §1222). Use calendar-day count, "
                "not year-fraction, for exact tier qualification.",
                "Options / warrants / SAFEs: holding period begins at exercise / "
                "conversion, not grant.",
                "Tacking rules in §1202(h)(1) cover gifts, §351 exchanges, and "
                "tax-free reorganizations. Other transfers (sale, redemption) "
                "break the holding period.",
                "CA does not conform to §1202. The holding-period tier only "
                "affects federal tax; California continues to tax at ordinary "
                "rates on the full gain.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "QSBS_ORIGINAL_ISSUANCE",
                "QSBS_OBBBA_TIERED",
                "QSBS_OBBBA_15M_CAP",
                "QSBS_1045_ROLLOVER",
                "QSBS_TACKING",
                "QSBS_STATE_CONFORMITY",
                "CA_NONCONFORMITY_QSBS",
            ],
            verification_confidence="high",
            computation_trace={
                "reference_date": str(ref_date),
                "obbba_effective_date": str(_OBBBA_EFFECTIVE_DATE),
                "lot_count": len(qsbs_lots),
                "lot_details": lot_details,
            },
        )
