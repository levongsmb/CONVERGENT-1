"""CGL_1231 — §1231 planning.

§1231 nets gains and losses from business-use depreciable real/personal
property and gains from certain involuntary conversions. Net §1231 GAIN
is treated as LTCG; net §1231 LOSS is ORDINARY. The five-year
§1231(c) recapture rule recharacterizes subsequent-year §1231 gains as
ordinary to the extent of prior-five-year net §1231 losses.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CGL_1231"
    CATEGORY_CODE = "CAPITAL_GAINS_LOSSES"
    PIN_CITES = [
        "IRC §1231(a)(1) — net §1231 gain treated as LTCG",
        "IRC §1231(a)(2) — net §1231 loss treated as ordinary",
        "IRC §1231(a)(3) — §1231 property definition",
        "IRC §1231(c) — five-year recapture of prior §1231 losses",
        "Treas. Reg. §1.1231-1 — netting procedure",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        # Collect §1231 activity from K-1s
        total_1231 = Decimal(0)
        sources: list = []
        for k1 in scenario.income.k1_income:
            if k1.section_1231_gain != Decimal(0):
                total_1231 += k1.section_1231_gain
                sources.append({
                    "entity_code": k1.entity_code,
                    "section_1231_gain": str(k1.section_1231_gain),
                })
        if total_1231 == Decimal(0):
            return self._not_applicable(
                "no §1231 gain or loss in scenario K-1s; §1231 planning is "
                "business-property-specific"
            )

        is_net_gain = total_1231 > Decimal(0)
        character = "LTCG" if is_net_gain else "ORDINARY_LOSS"

        # Approx differential
        if is_net_gain:
            # 23.8% LTCG+NIIT vs 37% ordinary on same dollar
            rate_differential = Decimal("0.37") - Decimal("0.238")
            differential_saving = (abs(total_1231) * rate_differential).quantize(Decimal("0.01"))
        else:
            # §1231 loss as ordinary offsets at top marginal 37% vs
            # capital loss limited to $3K/year against ordinary.
            # Ordinary-treatment value = loss × (37% - 0% effective on deferred cap)
            # First-order estimate: full loss × 0.37
            differential_saving = (abs(total_1231) * Decimal("0.37")).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=differential_saving,
            savings_by_tax_type=TaxImpact(
                capital_gains_tax=differential_saving if is_net_gain else Decimal(0),
                federal_income_tax=differential_saving if not is_net_gain else Decimal(0),
            ),
            inputs_required=[
                "prior five-year §1231 gain/loss history (for §1231(c) recapture)",
                "§1245 and §1250 recapture components per asset",
                "installment-sale posture if any §1231 gain is deferred",
                "§1033 involuntary-conversion elections if applicable",
            ],
            assumptions=[
                f"Aggregate §1231 posture: ${total_1231:,.2f}",
                f"Net character: {character}",
                "§1231(c) five-year lookback recharacterizes some GAIN as ordinary if prior net losses exist.",
                "First-order differential computed at 37% ordinary vs 23.8% LTCG+NIIT.",
            ],
            implementation_steps=[
                "Retrieve prior-five-year §1231 gain/loss ledger to apply "
                "§1231(c) recapture rule.",
                "Classify each disposition: §1231 property (business use, "
                "> 1-year hold) vs capital asset vs ordinary §1221.",
                "Separate §1245 ordinary recapture (machinery, equipment) "
                "from §1250 unrecaptured gain (real property) — see "
                "CGL_1250_UNRECAPTURED and RED_RECAPTURE_PLAN.",
                "Report net §1231 on Form 4797 Part I.",
            ],
            risks_and_caveats=[
                "§1231 is tested annually across all §1231 dispositions. "
                "Timing planning: consider bunching gains (net to LTCG) vs "
                "splitting (ordinary-loss year alone produces ordinary "
                "deduction).",
                "§1231(c) recapture adds friction to the 'whipsaw' strategy "
                "of alternating loss and gain years; prior losses convert "
                "subsequent gains to ordinary for five years.",
                "Installment sale of §1231 property: gain character is "
                "determined in year of sale per §453B; subsequent payments "
                "retain the year-of-sale character.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "CGL_1250_UNRECAPTURED",
                "RED_RECAPTURE_PLAN",
                "INST_STANDARD_453",
                "CGL_CARRYFORWARDS",
                "LL_461L",
            ],
            verification_confidence="high",
            computation_trace={
                "total_section_1231": str(total_1231),
                "character": character,
                "rate_differential_saving": str(differential_saving),
                "sources": sources,
            },
        )
