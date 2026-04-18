"""ENT_LLC_PSHIP_VS_SCORP — LLC taxed as partnership vs S corp comparison.

For a multi-member LLC currently taxed as a partnership with members
receiving SE-taxable allocations, the evaluator models whether flipping
to S-corp tax treatment (via Form 2553 with entity classification) would
reduce SE tax after offsetting costs: reasonable comp requirement,
state entity tax, loss of §743(b) / §754 flexibility, loss of special
allocations, loss of §1402(a)(13) limited-partner-ish posture where
applicable.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


_MIN_DISTRIBUTIVE_SHARE_FOR_APPLICABILITY = Decimal("100000")


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "ENT_LLC_PSHIP_VS_SCORP"
    CATEGORY_CODE = "ENTITY_SELECTION"
    PIN_CITES = [
        "IRC §7701 — entity classification under check-the-box",
        "Treas. Reg. §301.7701-3 — election to be classified as association (S corp)",
        "IRC §1402(a) — SECA on partnership distributive share",
        "IRC §1402(a)(13) — limited-partner exception",
        "Treas. Reg. §1.1402(a)-2 (proposed 1997) — not finalized",
        "Soroban Capital Partners LP v. Commissioner, 161 T.C. No. 12 (2023)",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        relevant_k1s = [
            k1 for k1 in scenario.income.k1_income
            if k1.entity_type == EntityType.LLC_PARTNERSHIP
            and k1.ordinary_business_income > _MIN_DISTRIBUTIVE_SHARE_FOR_APPLICABILITY
        ]
        if not relevant_k1s:
            return self._not_applicable(
                f"no LLC-as-partnership K-1 with distributive share above "
                f"${_MIN_DISTRIBUTIVE_SHARE_FOR_APPLICABILITY:,.0f}"
            )

        fica = rules.get("federal/fica_wage_bases", year)
        oasdi_base_raw = None
        se_multiplier = Decimal("0.9235")
        for p in fica.get("parameters", []):
            sp = p["coordinate"].get("sub_parameter")
            if sp == "oasdi_wage_base":
                oasdi_base_raw = p.get("value")
            elif sp == "se_earnings_multiplier" and p.get("value") is not None:
                se_multiplier = Decimal(str(p["value"]))

        if oasdi_base_raw is None:
            return StrategyResult(
                subcategory_code=self.SUBCATEGORY_CODE,
                applicable=True,
                reason=f"OASDI wage base for {year} awaiting SSA fact sheet",
                pin_cites=list(self.PIN_CITES),
                verification_confidence="low",
            )

        oasdi_base = Decimal(str(oasdi_base_raw))
        k1 = relevant_k1s[0]
        share = k1.ordinary_business_income + k1.guaranteed_payments
        se_net = share * se_multiplier

        current_se = (
            min(se_net, oasdi_base) * Decimal("0.124")
            + se_net * Decimal("0.029")
        ).quantize(Decimal("0.01"))

        # S corp anchor: reasonable comp at 40% of distributive share
        rc = (share * Decimal("0.40")).quantize(Decimal("0.01"))
        rc_fica = (
            min(rc, oasdi_base) * Decimal("0.124")
            + rc * Decimal("0.029")
        ).quantize(Decimal("0.01"))

        gross_savings = (current_se - rc_fica).quantize(Decimal("0.01"))
        ongoing_cost = Decimal("5000")
        net_savings = (gross_savings - ongoing_cost).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=max(net_savings, Decimal(0)),
            savings_by_tax_type=TaxImpact(
                self_employment_tax=current_se,
                payroll_tax=-rc_fica,
            ),
            inputs_required=[
                "distributive share and guaranteed payments by member",
                "member material participation and limited-partner facts",
                "current special allocations, §704(c) layers, §743(b) adjustments",
                "reasonable compensation baseline for each active member",
            ],
            assumptions=[
                f"OASDI wage base: ${oasdi_base:,.0f}",
                f"Evaluated member distributive share: ${share:,.2f}",
                f"Current SE tax on the share: ${current_se:,.2f}",
                f"S corp anchor reasonable comp (40%): ${rc:,.2f}",
                f"Post-S-corp FICA on reasonable comp: ${rc_fica:,.2f}",
                f"Ongoing compliance cost differential assumed: ${ongoing_cost:,.0f}",
            ],
            implementation_steps=[
                "Evaluate the §1402(a)(13) limited-partner posture BEFORE "
                "electing S status; if the member qualifies for the exception "
                "under Soroban-compliant facts, S election adds cost without "
                "benefit.",
                "Quantify the cost of losing partnership flexibility: special "
                "allocations, §743(b) step-up, §704(b) tax basis capital, "
                "§754 elections.",
                "If S election indicated: file Form 8832 then Form 2553 in the "
                "proper sequence; confirm entity classification change timing.",
                "Run COMP_REASONABLE_COMP for every active member who becomes "
                "an officer-shareholder.",
            ],
            risks_and_caveats=[
                "Converting partnership to S corp may trigger gain under "
                "§357(c) if partnership liabilities exceed member basis.",
                "S corp one-class-of-stock rule precludes preferred returns / "
                "waterfall structures common in partnership economics.",
                "If any member is an ineligible S shareholder (nonresident "
                "alien, trust not qualifying as ESBT/QSST, entity), S election "
                "is blocked.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "SET_SOROBAN_RISK",
                "SET_1402A13",
                "COMP_REASONABLE_COMP",
                "PTE_OUTSIDE_BASIS",
                "PS_SPECIAL_ALLOCATIONS",
                "SCSI_ONE_CLASS_STOCK",
                "SCSI_ESBT_QSST",
            ],
            verification_confidence="medium",
            computation_trace={
                "evaluated_entity": k1.entity_code,
                "distributive_share": str(share),
                "se_net_after_multiplier": str(se_net),
                "current_se_tax": str(current_se),
                "reasonable_comp_anchor": str(rc),
                "post_conversion_fica": str(rc_fica),
                "gross_savings": str(gross_savings),
                "ongoing_cost_assumed": str(ongoing_cost),
                "net_savings": str(net_savings),
            },
        )
