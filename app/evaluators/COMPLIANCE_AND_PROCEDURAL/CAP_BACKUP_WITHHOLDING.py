"""CAP_BACKUP_WITHHOLDING — backup withholding compliance."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_BACKUP_WITHHOLDING"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §3406 — backup withholding at 24%",
        "IRC §3406(a)(1) — triggering events (missing TIN, IRS B-notice)",
        "IRC §3406(f) — withholding agent liability",
        "Rev. Proc. 2021-48 — CP2100 / 972CG B-notice procedures",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        operating = [e for e in scenario.entities if e.type != EntityType.TRUST_GRANTOR]
        if not operating:
            return self._not_applicable(
                "no payor entity; backup withholding is payor-side"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "payee list with TIN match status",
                "any CP2100 or CP2100A notices received from IRS",
                "B-notice correspondence files",
                "1099 filings for affected payees",
            ],
            assumptions=[
                "Backup withholding rate: 24% on reportable payments to payees "
                "without valid TIN or under IRS B-notice.",
                "Withholding agent is personally liable under §3406(f) for "
                "failure to withhold.",
            ],
            implementation_steps=[
                "TIN match via IRS TIN Matching program or Form W-9 on file.",
                "On CP2100 / 2100A: send B-notice to payee within 15 business "
                "days and begin backup withholding until cured.",
                "Deposit withheld amounts and file Form 945 annually.",
                "Document cure actions in vendor file.",
            ],
            risks_and_caveats=[
                "Withholding agent is PERSONALLY liable for unwithheld amounts "
                "— not just the payee's tax.",
                "Second B-notice requires Social Security Administration or "
                "IRS verification letter from payee before withholding stops.",
            ],
            cross_strategy_impacts=[
                "CAP_1099",
                "CAP_W8_W9",
                "CAP_PAYROLL_REPORTING",
            ],
            verification_confidence="high",
        )
