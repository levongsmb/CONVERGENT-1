"""CAP_453D_ELECTION_OUT — election out of installment method under §453(d)."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_453D_ELECTION_OUT"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §453(d) — election out of installment method",
        "Treas. Reg. §15A.453-1(d) — timing and manner of election",
        "Rev. Proc. 92-29 — partial election out not permitted",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "planned installment sale facts (proceeds, basis, recapture)",
                "current-year marginal rate vs projected rate path",
                "§453A interest exposure analysis (> $5M receivable)",
                "available capital-loss carryforwards to offset accelerated gain",
            ],
            assumptions=[
                "§453(d) elect-out recognizes the entire gain in year of sale "
                "at the sale year's rates. Irrevocable without Commissioner "
                "consent.",
                "Election is all-or-nothing for a given disposition — not "
                "partial.",
            ],
            implementation_steps=[
                "Compute year-of-sale tax treating the sale as fully taxable "
                "vs spreading under §453.",
                "Decide based on: (a) rate trajectory, (b) available loss "
                "carryforwards, (c) §453A interest exposure, (d) state "
                "residency planning.",
                "Elect out by reporting the entire gain on the year-of-sale "
                "return (Form 6252 omitted, or marked as electing out).",
                "Document the election rationale in client file.",
            ],
            risks_and_caveats=[
                "Election is IRREVOCABLE without Commissioner consent.",
                "If the buyer defaults on future payments, the seller "
                "cannot reverse the election — and the original year's "
                "gain stands.",
            ],
            cross_strategy_impacts=[
                "INST_STANDARD_453",
                "INST_ELECTION_OUT",
                "CAP_PROTECTIVE_ELECTIONS",
                "CGL_CARRYFORWARDS",
            ],
            verification_confidence="high",
        )
