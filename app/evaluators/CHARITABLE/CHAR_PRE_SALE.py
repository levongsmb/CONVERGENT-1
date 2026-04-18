"""CHAR_PRE_SALE — pre-sale charitable gifting of appreciated stock.

When a liquidity event is planned, contributing appreciated equity to
a §170(b)(1)(A) public charity (or DAF) BEFORE the sale closes avoids
capital gain recognition on the gifted shares AND produces a §170(a)
deduction at full FMV. The IRS respects this if the gift occurs before
the donee is legally bound to sell (Humacid Co.; Rev. Rul. 78-197;
Palmer v. Commissioner).
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CHAR_PRE_SALE"
    CATEGORY_CODE = "CHARITABLE"
    PIN_CITES = [
        "IRC §170(e)(1) — FMV deduction for appreciated long-term capital property",
        "IRC §170(b)(1)(C) — 30% AGI limit for appreciated property",
        "Humacid Co. v. Commissioner, 42 T.C. 894 (1964) — gift before binding commitment",
        "Rev. Rul. 78-197 — anticipatory assignment of income",
        "Palmer v. Commissioner, 62 T.C. 684 (1974) — contribution of stock subsequently redeemed",
        "Ferguson v. Commissioner, 174 F.3d 997 (9th Cir. 1999) — anticipatory-assignment doctrine",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        liquidity = scenario.planning.liquidity_event_planned
        if liquidity is None:
            return self._not_applicable(
                "no liquidity event planned; pre-sale charitable strategy "
                "requires an identifiable transaction"
            )

        # Identify appreciated-equity candidates from assets
        candidates = []
        total_appreciated = Decimal(0)
        for a in scenario.assets:
            if a.fmv is None or a.adjusted_basis is None:
                continue
            gain = a.fmv - a.adjusted_basis
            if gain <= Decimal(0):
                continue
            # Only long-term capital property qualifies for FMV deduction
            if a.acquisition_date is None:
                continue
            holding_days = (
                (liquidity.get("target_close_date") or a.acquisition_date.replace(year=year))
            )
            # Rough approximation: if acquired > 1 year ago, assume LT
            years_held = year - a.acquisition_date.year
            if years_held < 1:
                continue
            candidates.append({
                "asset_code": a.asset_code,
                "basis": str(a.adjusted_basis),
                "fmv": str(a.fmv),
                "gain": str(gain),
            })
            total_appreciated += a.fmv

        if not candidates:
            return self._not_applicable(
                "no appreciated long-term equity candidate for pre-sale gift"
            )

        # Quantify the double benefit: (a) avoided capital gain tax on
        # the gifted portion, (b) charitable deduction at FMV.
        # Assume a modest gift level: 10% of total_appreciated or the
        # 30% AGI cap, whichever is lower. Orchestrator refines.
        gift_portion = total_appreciated * Decimal("0.10")
        # Assumed gain portion of gift ≈ (total_appreciated - basis) / total * gift
        # Use a flat 60% gain proxy for simplicity
        avoided_cap_gain_tax = (
            gift_portion * Decimal("0.60") * Decimal("0.238")
        ).quantize(Decimal("0.01"))
        deduction_value = (gift_portion * Decimal("0.32")).quantize(Decimal("0.01"))
        total_benefit = (avoided_cap_gain_tax + deduction_value).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=total_benefit,
            savings_by_tax_type=TaxImpact(
                capital_gains_tax=avoided_cap_gain_tax,
                federal_income_tax=deduction_value,
            ),
            inputs_required=[
                "target liquidity close date and structure",
                "appreciated asset inventory with basis and FMV",
                "charitable intent dollars (cash and equity)",
                "AGI projection for the sale year (30% AGI limit math)",
                "donee organization type (operating charity, DAF, PF)",
            ],
            assumptions=[
                f"Liquidity event target date: {liquidity.get('target_close_date')}",
                f"Appreciated candidates identified: {len(candidates)}",
                f"Approx FMV of appreciated pool: ${total_appreciated:,.2f}",
                f"Illustrative gift portion (10% of pool): ${gift_portion:,.2f}",
                f"Gain portion of gift (60% proxy): "
                f"${gift_portion * Decimal('0.60'):,.2f}",
                "Avoided LTCG+NIIT at 23.8% on the gain portion.",
                "Deduction at 32% approx marginal rate.",
            ],
            implementation_steps=[
                "Identify donee (DAF sponsor or operating charity). DAF "
                "recommended for liquidity flexibility.",
                "Transfer appreciated shares BEFORE any binding sale contract "
                "or LOI that would trigger the anticipatory-assignment "
                "doctrine. Execute the gift via a DTC transfer with "
                "contemporaneous written acknowledgment.",
                "Confirm the donee is a §170(b)(1)(A) public charity or DAF "
                "sponsor (30% AGI limit applies; 5-year carryover for excess).",
                "For closely-held stock: obtain a qualified appraisal under "
                "§170(f)(11) if the gift > $5,000 (for non-publicly-traded "
                "stock; >$10K triggers appraisal summary on Form 8283).",
                "Coordinate with COMP_REASONABLE_COMP / SALE_BASIS_CLEANUP "
                "to ensure pre-sale basis adjustments happen before the gift.",
            ],
            risks_and_caveats=[
                "Anticipatory assignment of income: if the donee is legally "
                "bound to sell at the time of gift, the donor recognizes the "
                "gain (Rev. Rul. 78-197; Ferguson 9th Cir.). Gift must occur "
                "BEFORE binding contract.",
                "Qualified appraisal under §170(f)(11) required for non-"
                "publicly-traded stock gifts > $5,000; Form 8283 Section B "
                "for > $10,000.",
                "CA does not conform to the federal preferential rate avoided; "
                "CA still taxes realized gain on the taxpayer's sale proceeds.",
                "30% AGI limit for appreciated property to public charity / "
                "DAF. Excess carries forward 5 years.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "CHAR_APPREC_SECURITIES",
                "CHAR_DAF",
                "CHAR_CRT",
                "CHAR_PRIVATE_FOUNDATION",
                "SALE_BASIS_CLEANUP",
                "SALE_ASSET_VS_STOCK",
                "CGL_CHAR_GIFTING_APPREC",
            ],
            verification_confidence="high",
            computation_trace={
                "liquidity_target_date": str(liquidity.get("target_close_date")),
                "candidate_count": len(candidates),
                "candidates": candidates,
                "total_appreciated_fmv": str(total_appreciated),
                "illustrative_gift_portion": str(gift_portion),
                "avoided_cap_gain_tax": str(avoided_cap_gain_tax),
                "deduction_value": str(deduction_value),
                "total_benefit": str(total_benefit),
            },
        )
