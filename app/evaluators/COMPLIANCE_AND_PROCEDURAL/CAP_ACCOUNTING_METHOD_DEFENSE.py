"""CAP_ACCOUNTING_METHOD_DEFENSE — accounting method defense in examination."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_ACCOUNTING_METHOD_DEFENSE"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §446(b) — Commissioner's authority to require change of method",
        "IRC §481(a) — spread on method change",
        "Treas. Reg. §1.446-1(e) — consistent treatment requirement",
        "IRM 4.11.6 — examination-initiated method changes",
        "Rev. Proc. 2002-9 — non-automatic method changes",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "current method documentation",
                "consistency-of-treatment evidence (multiple prior years)",
                "agent's proposed method change and §481(a) adjustment",
                "scope of agent's authority (method change vs one-year adjustment)",
            ],
            assumptions=[
                "Method adopted + treated consistently is the taxpayer's "
                "method even if technically incorrect; change requires §446(e) "
                "consent or §446(b) agent action.",
                "Agent-initiated method change carries a 4-year §481(a) "
                "spread that is less favorable than voluntary change.",
            ],
            implementation_steps=[
                "Document the taxpayer's existing method with 3+ years of "
                "consistent application.",
                "Challenge agent's §446(b) action: argue the existing method "
                "clearly reflects income.",
                "If change is unavoidable, negotiate voluntary filing of "
                "Form 3115 pre-exam to secure audit protection.",
                "Negotiate §481(a) amount and spread terms at Appeals.",
            ],
            risks_and_caveats=[
                "Voluntary method change under Rev. Proc. 2023-24 BEFORE exam "
                "opens audit protection; once exam issues IDR on the method, "
                "audit protection closes.",
                "§481(a) unfavorable adjustments imposed by exam may not be "
                "spread; Rev. Rul. 90-38 allows 4-year spread only for "
                "voluntary changes.",
            ],
            cross_strategy_impacts=[
                "CAP_EXAMS_APPEALS",
                "CAP_3115_METHOD_CHANGE",
                "AM_481A_PLANNING",
            ],
            verification_confidence="high",
        )
