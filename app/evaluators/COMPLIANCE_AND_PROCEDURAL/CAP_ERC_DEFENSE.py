"""CAP_ERC_DEFENSE — Employee Retention Credit examination defense."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_ERC_DEFENSE"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "CARES Act §2301, as amended — Employee Retention Credit",
        "Rev. Proc. 2021-33 — gross receipts test",
        "Notice 2021-20, Notice 2021-23, Notice 2021-49 — IRS guidance",
        "IR-2023-169 — ERC moratorium on new claims",
        "IR-2024-203 — ERC voluntary disclosure program 2.0",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "ERC claim history by quarter (2020 Q2-Q4, 2021 Q1-Q3)",
                "gross receipts decline test or full/partial suspension documentation",
                "qualified wages and health plan expense detail",
                "copies of Form 941-X submitted",
                "amended income tax returns reflecting §280C wage reduction",
            ],
            assumptions=[
                "ERC audits are a 2024-2026 IRS enforcement priority post-"
                "moratorium (IR-2023-169).",
                "Voluntary disclosure program (VDP 2.0) allows 85% clawback "
                "repayment with no penalty if settled before IRS audit.",
                "§280C wage-reduction requirement: ERC-claimed wages cannot "
                "also be deducted on income tax return.",
            ],
            implementation_steps=[
                "Audit internal ERC claim documentation for each quarter.",
                "Validate gross receipts decline per quarter or suspension "
                "facts per order.",
                "If claim is indefensible: evaluate VDP 2.0 before exam notice.",
                "If claim is defensible: prepare substantiation package "
                "(orders, HR records, payroll detail, revenue evidence).",
                "File amended income tax returns to reduce §280C wages if not "
                "already done.",
            ],
            risks_and_caveats=[
                "IRS has signaled aggressive enforcement; penalties up to "
                "75% of erroneous claim plus interest.",
                "Preparer §6694 penalties apply to ERC advisors; document "
                "reliance only on sources with substantial authority.",
                "VDP 2.0 closes on specific IRS deadlines — track cutoffs.",
            ],
            cross_strategy_impacts=[
                "CAP_EXAMS_APPEALS",
                "CAP_REASONABLE_CAUSE",
                "CAP_PENALTY_ABATEMENT",
            ],
            verification_confidence="high",
        )
