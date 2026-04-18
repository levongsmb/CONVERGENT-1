"""CAP_RECORD_RECONSTRUCTION — record reconstruction and substantiation protocols."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_RECORD_RECONSTRUCTION"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §6001 — records and returns required",
        "Treas. Reg. §1.6001-1 — recordkeeping standards",
        "Cohan v. Commissioner, 39 F.2d 540 (2d Cir. 1930) — reasonable estimation",
        "IRC §274(d) — strict substantiation for travel, meals, gifts, listed property",
        "IRM 4.10.7 — examination standards",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "identified records destroyed / unavailable",
                "third-party sources (bank statements, vendors, customers)",
                "§274(d) items with strict-substantiation requirements",
                "pattern-of-business evidence for Cohan rule",
            ],
            assumptions=[
                "Cohan rule permits reasonable estimation for most "
                "deductions, but §274(d) requires strict substantiation for "
                "travel, meals, gifts, and listed property.",
                "Reconstruction is admissible; contemporaneous is preferred.",
            ],
            implementation_steps=[
                "Request bank, credit card, vendor, customer records to "
                "reconstruct transaction flows.",
                "For §274(d) items: if no records, deduction is disallowed — "
                "NO Cohan relief.",
                "Prepare written reconstruction memo with methodology and "
                "third-party source references.",
                "Retain reconstruction workpapers in permanent file.",
            ],
            risks_and_caveats=[
                "§274(d) strict substantiation is NON-negotiable; no "
                "estimation permitted.",
                "Reconstruction subject to audit scrutiny; keep methodology "
                "reasonable and documented.",
            ],
            cross_strategy_impacts=[
                "CAP_REASONABLE_CAUSE",
                "CAP_EXAMS_APPEALS",
                "CAP_7508A_DISASTER",
            ],
            verification_confidence="high",
        )
