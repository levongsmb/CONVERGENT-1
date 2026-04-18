"""SSALT_164_SALT_CAP — SALT cap planning under §164 (high-level framework).

Companion to SSALT_OBBBA_CAP_MODELING (detailed phaseout arithmetic)
and CHAR_OBBBA_37_CAP. This evaluator surfaces general SALT-cap
planning patterns: PTET as workaround, property-tax timing, sales-tax
election for no-income-tax states.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_164_SALT_CAP"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "IRC §164(a) — state and local taxes generally deductible",
        "IRC §164(b)(6) — SALT cap as amended by OBBBA",
        "Treas. Reg. §1.164-1 — timing of deduction",
        "Notice 2020-75 — PTET workaround blessed",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        total_salt = (
            scenario.deductions.salt_paid_state_income
            + scenario.deductions.salt_paid_property_residence
            + scenario.deductions.salt_paid_sales_tax
        )
        if total_salt <= Decimal(0):
            return self._not_applicable(
                "no SALT payments in scenario; §164 cap analysis not relevant"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "SALT paid by category (state income, property residence, sales)",
                "§164(b)(6) base cap and phaseout posture (see SSALT_OBBBA_CAP_MODELING)",
                "PTET availability per state (see SSALT_PTET_MODELING)",
                "ability to elect sales tax deduction for no-income-tax residents",
            ],
            assumptions=[
                "SALT cap applies only to itemized-deduction-level SALT.",
                "Property taxes on investment-use property are NOT capped "
                "(flow to Schedule E).",
                "PTET shifts state income tax from capped individual to "
                "deductible entity-level.",
            ],
            implementation_steps=[
                "Allocate SALT deductions between capped (personal use) and "
                "uncapped (investment / business).",
                "Where state-income component is large, coordinate with "
                "SSALT_PTET_MODELING to shift into entity-level deduction.",
                "For no-income-tax-state residents: evaluate sales-tax "
                "election per IRS Schedule A instructions.",
                "For property tax: time large payments into a year where "
                "MAGI is below §164(b)(6) phaseout to preserve cap.",
            ],
            risks_and_caveats=[
                "OBBBA phaseout and 2030 reversion require multi-year modeling.",
                "PTET workaround reduces taxpayer's federal income BUT shifts "
                "cash to the entity; balance against owner liquidity.",
            ],
            cross_strategy_impacts=[
                "SSALT_OBBBA_CAP_MODELING",
                "SSALT_PTET_MODELING",
                "SSALT_PROPERTY_TAX_TIMING",
                "CHAR_OBBBA_37_CAP",
                "CA_PTET_ELECTION",
            ],
            verification_confidence="high",
        )
