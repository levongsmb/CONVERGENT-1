"""AM_481A_PLANNING — §481(a) spread planning on method changes.

§481(a) adjustments arise when an accounting method is changed. The
adjustment may be POSITIVE (income pickup — unfavorable, spread over 4
years) or NEGATIVE (income reduction — favorable, recognized in the
year of change). Planning includes timing the method change, choosing
between automatic and non-automatic procedures, and coordinating with
other planning actions (e.g., R&D method change, cost seg, §174A).
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "AM_481A_PLANNING"
    CATEGORY_CODE = "ACCOUNTING_METHODS"
    PIN_CITES = [
        "IRC §481(a) — adjustment for change in accounting method",
        "IRC §446(e) — Commissioner consent for method change",
        "Rev. Proc. 2015-13 — general change-of-accounting-method procedures",
        "Rev. Proc. 2023-24 — automatic method change list",
        "Treas. Reg. §1.481-1 — positive and negative §481(a) adjustments",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        # Applicable when scenario has at least one operating entity that
        # could make a method change in the planning year. In practice, this
        # evaluator is a companion to the entity-level method change
        # evaluators (AM_CASH_VS_ACCRUAL, AM_174A_DOMESTIC_RE,
        # RED_COST_SEG, etc.) — it surfaces the cross-cutting §481(a)
        # mechanics.
        ops = [
            e for e in scenario.entities
            if e.type in (
                EntityType.S_CORP, EntityType.LLC_S_CORP,
                EntityType.C_CORP, EntityType.LLC_C_CORP,
                EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
                EntityType.SOLE_PROP,
            )
        ]
        if not ops:
            return self._not_applicable(
                "no operating entity; §481(a) applies at the entity / "
                "Schedule C level"
            )

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "specific method changes being evaluated (cash vs accrual, "
                "§471(c) inventory, §174A R&E, cost seg, §263A) ",
                "computed §481(a) adjustment amount per change",
                "sign of the adjustment (positive unfavorable / negative favorable)",
                "taxpayer's marginal rate path for the 4-year unfavorable spread",
                "coordination with §461(l) EBL if favorable adjustment creates a loss",
            ],
            assumptions=[
                f"Candidate entities for method changes: {len(ops)}",
                "Positive §481(a) (unfavorable): spread over 4 years.",
                "Negative §481(a) (favorable): immediate in year of change.",
                "Short-year cutoffs: final-year method change recognizes "
                "the full §481(a) in the short year.",
            ],
            implementation_steps=[
                "Compute the §481(a) adjustment for each proposed method "
                "change before deciding on the change year.",
                "Batch multiple method changes where possible: a single "
                "Form 3115 can cover multiple changes on automatic consent.",
                "Time unfavorable §481(a) into a year with low marginal "
                "rate (e.g., an NOL year, a pre-retirement year, a year of "
                "extended §461(l) EBL available).",
                "For favorable §481(a) that exceeds current-year §461(l) "
                "threshold, the excess becomes §172 NOL.",
                "File Form 3115 attaching schedule of §481(a) computation; "
                "retain supporting workpapers for 3 years after the method "
                "change.",
            ],
            risks_and_caveats=[
                "§481(a) spread is interrupted by disposition of the "
                "entity, death of the taxpayer, or subsequent method "
                "change — remaining balance accelerates.",
                "BBA audit regime applies to §481(a) adjustments at the "
                "partnership level — plan for partnership representative "
                "elections.",
                "Some method changes are NON-automatic (require IRS "
                "consent before filing) — plan the timing 12+ months in "
                "advance.",
                "User-fee schedule under Rev. Proc. 2015-13 updated "
                "periodically; confirm current fees before filing.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "AM_CASH_VS_ACCRUAL",
                "AM_471C_INVENTORY",
                "AM_174A_DOMESTIC_RE",
                "AM_263A_UNICAP",
                "AM_448_GROSS_RECEIPTS",
                "RED_COST_SEG",
                "LL_461L",
                "LL_NOL_USAGE",
                "CAP_3115_METHOD_CHANGE",
            ],
            verification_confidence="high",
            computation_trace={
                "candidate_entity_count": len(ops),
                "candidate_entity_codes": [e.code for e in ops],
            },
        )
