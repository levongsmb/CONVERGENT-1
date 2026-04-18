"""CHAR_APPREC_SECURITIES — direct appreciated-securities gifting.

Gift appreciated long-term stock directly to a §170(b)(1)(A) public
charity or DAF instead of selling and donating cash. The taxpayer gets
a §170(a) deduction at FMV AND avoids the capital gain that would
otherwise be recognized. Compare to a cash gift funded by the after-tax
proceeds of the same stock sale.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import AssetType, ClientScenario


_GIFTABLE_TYPES = {AssetType.STOCK_PUBLIC, AssetType.CRYPTO}


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CHAR_APPREC_SECURITIES"
    CATEGORY_CODE = "CHARITABLE"
    PIN_CITES = [
        "IRC §170(e)(1)(A) — FMV deduction for appreciated LT capital gain property",
        "IRC §170(b)(1)(C) — 30% AGI limit to public charity / DAF",
        "IRC §170(b)(1)(D) — 20% AGI limit for gifts to non-operating PF",
        "IRC §170(e)(1)(B)(ii) — basis-only deduction for non-publicly-traded stock to PF",
        "Treas. Reg. §1.170A-13 — substantiation requirements",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        candidates = []
        total_gain = Decimal(0)
        total_fmv = Decimal(0)
        for a in scenario.assets:
            if a.asset_type not in _GIFTABLE_TYPES:
                continue
            if a.fmv is None or a.adjusted_basis is None:
                continue
            gain = a.fmv - a.adjusted_basis
            if gain <= Decimal(0):
                continue
            if a.acquisition_date is None:
                continue
            years_held = year - a.acquisition_date.year
            if years_held < 1:
                continue
            candidates.append({
                "asset_code": a.asset_code,
                "description": a.description,
                "basis": str(a.adjusted_basis),
                "fmv": str(a.fmv),
                "gain": str(gain),
                "years_held": years_held,
            })
            total_gain += gain
            total_fmv += a.fmv

        if not candidates:
            return self._not_applicable(
                "no appreciated long-term publicly-traded stock or crypto "
                "in scenario; direct gifting requires LT-held appreciated property"
            )

        # If no existing charitable intent, surface opportunity without
        # quantifying a dollar benefit
        current_charitable_cash = (
            scenario.deductions.charitable_cash_public
            + scenario.deductions.charitable_cash_daf
        )

        # Illustrative: shift $25,000 of current cash giving to appreciated
        # securities (or donate the equivalent that would otherwise be cash).
        # The benefit = avoided cap gain × 23.8% on the gain portion.
        gift_illustration = min(current_charitable_cash, total_fmv)
        if gift_illustration == Decimal(0) and total_fmv > Decimal(0):
            gift_illustration = min(total_fmv * Decimal("0.10"), Decimal("25000"))
        # Gain portion assumed proportional to total_gain / total_fmv
        if total_fmv > Decimal(0):
            gain_pct = (total_gain / total_fmv)
        else:
            gain_pct = Decimal(0)
        illustrated_gain = (gift_illustration * gain_pct).quantize(Decimal("0.01"))
        avoided_cap_gain_tax = (illustrated_gain * Decimal("0.238")).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=avoided_cap_gain_tax,
            savings_by_tax_type=TaxImpact(capital_gains_tax=avoided_cap_gain_tax),
            inputs_required=[
                "specific lots and basis per gifted position",
                "donee 501(c)(3) classification (public charity vs PF)",
                "AGI projection for 30% cap modeling",
                "custodian DTC transfer capability",
            ],
            assumptions=[
                f"Appreciated LT stock / crypto candidates: {len(candidates)}",
                f"Aggregate unrealized gain: ${total_gain:,.2f}",
                f"Aggregate FMV: ${total_fmv:,.2f}",
                f"Illustrative gift amount: ${gift_illustration:,.2f}",
                f"Illustrated gain portion avoided: ${illustrated_gain:,.2f}",
                "Avoided LTCG+NIIT at 23.8% on the gain portion.",
            ],
            implementation_steps=[
                "Select high-basis-delta lots (largest unrealized gain %); "
                "donate those, not cash.",
                "Coordinate with custodian on DTC transfer to donee.",
                "Obtain contemporaneous written acknowledgment under "
                "§170(f)(8) within deadlines.",
                "Form 8283 required if total noncash > $500; Section B + "
                "qualified appraisal for non-publicly-traded stock > $10,000.",
                "Track 30% AGI limit with 5-year carryforward for any excess.",
            ],
            risks_and_caveats=[
                "Only publicly-traded stock receives FMV deduction without an "
                "appraisal. Non-publicly-traded stock gifts require §170(f)(11) "
                "qualified appraisal and Form 8283 Section B.",
                "Gifts to non-operating private foundations are limited to 20% "
                "AGI and to BASIS (not FMV) for non-publicly-traded stock per "
                "§170(e)(1)(B)(ii).",
                "Crypto is classified as property, not currency; same §170(e)(1) "
                "FMV rules apply to LT-held positions.",
                "Short-term gain property reduces the deduction by the gain "
                "portion under §170(e)(1)(A).",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "CHAR_DAF",
                "CHAR_PRE_SALE",
                "CHAR_BUNCHING",
                "CHAR_AGI_LIMITS",
                "CGL_CHAR_GIFTING_APPREC",
                "CGL_TAX_LOSS_HARVEST",
            ],
            verification_confidence="high",
            computation_trace={
                "candidate_count": len(candidates),
                "candidates": candidates,
                "aggregate_unrealized_gain": str(total_gain),
                "aggregate_fmv": str(total_fmv),
                "current_charitable_cash": str(current_charitable_cash),
                "illustrative_gift_amount": str(gift_illustration),
                "gain_portion_avoided": str(illustrated_gain),
                "avoided_cap_gain_tax": str(avoided_cap_gain_tax),
            },
        )
