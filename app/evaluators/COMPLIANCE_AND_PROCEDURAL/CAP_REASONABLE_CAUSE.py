"""CAP_REASONABLE_CAUSE — reasonable cause substantiation."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_REASONABLE_CAUSE"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §6651(a) — reasonable cause not due to willful neglect",
        "IRC §6664(c) — reasonable cause for accuracy penalties",
        "Treas. Reg. §301.6651-1(c) — ordinary business care and prudence",
        "IRM 20.1.1.3.2 — reasonable cause framework",
        "Boyle v. United States, 469 U.S. 241 (1985) — reliance on professional",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "timeline of events causing the compliance failure",
                "documentary evidence (medical records, disaster declaration, etc.)",
                "written advice from tax professional if reliance is asserted",
                "taxpayer's compliance history",
            ],
            assumptions=[
                "IRM 20.1.1.3.2 factors: death / serious illness, unavoidable "
                "absence, destruction of records, reliance on professional, "
                "inability to obtain records.",
                "Boyle: reliance on professional does NOT excuse missed filing "
                "deadline; only the substantive advice is protected.",
            ],
            implementation_steps=[
                "Draft facts statement using IRM 20.1.1.3.2 factor framework.",
                "Attach supporting documents (medical, disaster, third-party).",
                "File Form 843 or respond to notice with abatement request.",
                "If denied, escalate via Appeals under IRM 20.1.1.4.",
            ],
            risks_and_caveats=[
                "Boyle-limited reliance defense: reliance on professional for "
                "substantive interpretation is reasonable cause; reliance on "
                "professional to MEET A DEADLINE is not.",
                "§6664(c) reasonable cause for accuracy penalties also "
                "requires good faith.",
            ],
            cross_strategy_impacts=[
                "CAP_PENALTY_ABATEMENT",
                "CAP_FIRST_TIME_ABATE",
                "CAP_EXAMS_APPEALS",
            ],
            verification_confidence="high",
        )
