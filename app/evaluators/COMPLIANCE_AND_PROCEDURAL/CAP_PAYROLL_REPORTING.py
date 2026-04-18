"""CAP_PAYROLL_REPORTING — payroll reporting compliance."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_PAYROLL_REPORTING"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §3101 / §3111 — FICA reporting",
        "IRC §3301 — FUTA",
        "IRC §6672 — trust-fund recovery penalty (100% of unpaid)",
        "Form 941 quarterly / Form 940 annual",
        "Form W-2 / W-3 annual",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        employers = [
            e for e in scenario.entities
            if e.type in (
                EntityType.S_CORP, EntityType.LLC_S_CORP,
                EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
                EntityType.C_CORP, EntityType.LLC_C_CORP,
            )
            and e.w2_wages > Decimal(0)
        ]
        if not employers:
            return self._not_applicable(
                "no W-2-paying entity in scenario"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "Forms 941 quarterly filing history",
                "Form 940 annual filing",
                "W-2 / W-3 filing status with SSA",
                "state payroll returns (CA DE-9, DE-9C)",
                "EFTPS deposit schedule (monthly vs semi-weekly)",
            ],
            assumptions=[
                "§6672 Trust Fund Recovery Penalty is 100% of unpaid trust "
                "fund taxes (employee withholding); applies personally to "
                "responsible persons.",
                "Deposit schedule determined by $50,000 lookback-period rule.",
                "State returns (CA DE-9 / DE-9C) are SEPARATE filings.",
            ],
            implementation_steps=[
                "Automate payroll via licensed provider (Gusto, Rippling, ADP) "
                "with tax deposits and quarterly filings included.",
                "Reconcile W-2 totals to 941 totals quarterly.",
                "Deliver W-2s to employees and W-3 to SSA by January 31.",
                "Maintain Form 941 and state filings in permanent file.",
            ],
            risks_and_caveats=[
                "§6672 TFRP can attach personally to any responsible "
                "person who willfully failed to pay over trust fund taxes.",
                "Unfiled 941s are a top IRS enforcement target; automated "
                "collection begins quickly.",
            ],
            cross_strategy_impacts=[
                "COMP_PAYROLL_TAX_MIN",
                "COMP_WORKER_CLASSIFICATION",
                "CAP_1099",
                "CAP_BACKUP_WITHHOLDING",
            ],
            verification_confidence="high",
        )
