"""CAP_IDENTITY_POA — identity theft, transcript, and POA procedures."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_IDENTITY_POA"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §7602 — examination authority and POA access",
        "Form 2848 — Power of Attorney and Declaration of Representative",
        "Form 8821 — Tax Information Authorization",
        "Form 14039 — Identity Theft Affidavit",
        "IRM 10.5.3 — identity protection procedures",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "transcripts needed (return, wage, account)",
                "identity theft indicators (unexpected notice, rejected e-file)",
                "existing POA / TIA filings with CAF number",
            ],
            assumptions=[
                "Form 2848 is required for representation authority; Form "
                "8821 is sufficient for transcript access.",
                "IP PIN issued by IRS is required for e-file if identity "
                "theft flagged.",
            ],
            implementation_steps=[
                "File Form 2848 or 8821 with CAF unit to establish authority.",
                "Request transcripts via IRS e-Services, Practitioner "
                "Priority Service, or Transcript Delivery System.",
                "If identity theft suspected: file Form 14039 immediately; "
                "request IP PIN; lock down transcripts.",
                "Retain CAF numbers and POA expiration dates in client file.",
            ],
            risks_and_caveats=[
                "POA / TIA has annual expiration cycles; renewal triggers "
                "should be tracked.",
                "IP PIN once issued must be used on every return or e-file "
                "will reject.",
            ],
            cross_strategy_impacts=[
                "CAP_EXAMS_APPEALS",
                "CAP_STATUTE_MGMT",
            ],
            verification_confidence="high",
        )
