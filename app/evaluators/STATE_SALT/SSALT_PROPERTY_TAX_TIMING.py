"""SSALT_PROPERTY_TAX_TIMING — property tax timing and prepayment analysis."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_PROPERTY_TAX_TIMING"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "IRC §164(b)(6) — SALT cap",
        "Treas. Reg. §1.164-1 — cash-basis deduction timing",
        "IRS FAQ on 2017 prepayment — assessment requirement",
        "Rev. Rul. 2002-1 — escrow payments timing",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        property_tax = scenario.deductions.salt_paid_property_residence
        if property_tax <= Decimal(0):
            return self._not_applicable(
                "no property tax payments in scenario"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "property tax assessment amount for each jurisdiction",
                "installment due dates per jurisdiction",
                "projected MAGI by year to locate §164(b)(6) phaseout sweet spot",
                "escrow account balance and ability to control timing",
            ],
            assumptions=[
                "Cash-basis individuals deduct property tax when ACTUALLY paid, "
                "provided it has been ASSESSED — prepayments of unassessed "
                "taxes are non-deductible (IRS FAQ).",
                "SALT cap ordering: property + state-income + sales all "
                "compete for the same capped amount.",
            ],
            implementation_steps=[
                "Obtain property-tax bills showing the assessment year.",
                "Time payments into the year where (a) SALT cap has headroom "
                "and (b) MAGI is below §164(b)(6) phaseout.",
                "Bunch property tax payments into alternating years to "
                "stack SALT deductions above the standard-deduction floor.",
                "For escrow accounts: some lenders allow pay-through timing; "
                "coordinate with loan servicer.",
            ],
            risks_and_caveats=[
                "Prepayment of taxes not yet assessed is NOT deductible "
                "(2017 IRS FAQ).",
                "Property tax on INVESTMENT property is NOT capped under "
                "§164(b)(6); ensure allocation is accurate.",
            ],
            cross_strategy_impacts=[
                "SSALT_164_SALT_CAP",
                "SSALT_OBBBA_CAP_MODELING",
                "CHAR_BUNCHING",
            ],
            verification_confidence="high",
        )
