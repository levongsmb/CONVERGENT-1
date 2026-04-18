"""CAP_3115_METHOD_CHANGE — method change filing procedures (Form 3115)."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_3115_METHOD_CHANGE"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §446(e) — Commissioner consent for method change",
        "IRC §481(a) — spread adjustment on method change",
        "Rev. Proc. 2015-13 — general procedures for automatic and non-automatic changes",
        "Rev. Proc. 2023-24 — current automatic method change list",
        "Form 3115 instructions",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "list of method changes being pursued (DCNs or non-automatic)",
                "computed §481(a) adjustment per change",
                "attachment of original-method and new-method detail",
                "audit-protection status for the change year",
            ],
            assumptions=[
                "Automatic change via Rev. Proc. 2023-24 DCN list: file Form "
                "3115 by original return due date (including extensions); "
                "duplicate copy to Ogden IRS by same date.",
                "Non-automatic change: file by end of the year of change; "
                "user-fee and advance-consent required.",
                "§481(a): positive (income) spread over 4 years; negative "
                "(deduction) immediate.",
            ],
            implementation_steps=[
                "Identify DCN from Rev. Proc. 2023-24; confirm automatic "
                "vs non-automatic track.",
                "Compute §481(a) with workpaper support per method change.",
                "Prepare Form 3115 with required sections (Part I, II, IV "
                "plus DCN-specific schedule).",
                "File in duplicate per procedure (one with return, one to "
                "Ogden).",
                "Retain workpapers for 3 years after change takes effect.",
            ],
            risks_and_caveats=[
                "Missing the automatic-change deadline forfeits audit "
                "protection; non-automatic consent may be the only remedy.",
                "Some changes (§168(k) bonus, §174 capitalization) are not "
                "properly method changes — they are elections or "
                "transactions. Classification matters.",
            ],
            cross_strategy_impacts=[
                "AM_481A_PLANNING",
                "AM_CASH_VS_ACCRUAL",
                "AM_174A_DOMESTIC_RE",
                "AM_471C_INVENTORY",
                "RED_COST_SEG",
            ],
            verification_confidence="high",
        )
