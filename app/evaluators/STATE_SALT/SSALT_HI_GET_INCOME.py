"""SSALT_HI_GET_INCOME — Hawaii GET (general excise tax) and income
tax overlap / stacking analysis."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, StateCode


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_HI_GET_INCOME"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "HRS §237-13 — Hawaii General Excise Tax imposition",
        "HRS §237-14.5 — GET on wholesale",
        "HRS §235-1 et seq. — Hawaii income tax",
        "Hawaii DOTAX Announcement 2025 series — nexus and GET pass-through",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        hi_nexus = (
            scenario.identity.primary_state_domicile == StateCode.HI
            or any(
                e.formation_state == StateCode.HI
                or StateCode.HI in (e.operating_states or [])
                for e in scenario.entities
            )
        )
        if not hi_nexus:
            return self._not_applicable(
                "no Hawaii domicile or Hawaii-sourced business activity; "
                "HI GET applies only to HI-nexus receipts"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "HI gross receipts by activity class (retail, wholesale, services)",
                "GET license and county surcharge posture",
                "HI income tax liability on same activity",
                "client contract language on GET pass-through to customer",
            ],
            assumptions=[
                "HI GET is NOT a sales tax; it is a tax on the seller that "
                "cannot be fully excluded from income. Base 4% (retail) + "
                "county surcharge (Oahu 4.5% combined).",
                "GET paid is deductible as business expense for HI income tax "
                "but NOT passed through cleanly — creates stacking.",
                "GET pass-through to customer (invoice stated) is not a "
                "true reimbursement; HI treats gross-up receipts as taxable.",
            ],
            implementation_steps=[
                "Register for GET license (G-49 annual return); monthly or "
                "semi-annual periodic returns per threshold.",
                "Structure pricing to gross-up GET on customer invoices; "
                "GET-on-GET applies (tax-on-tax).",
                "Coordinate HI income tax — GET paid deductible; avoid "
                "double-booking.",
                "For multi-state clients, document HI nexus and "
                "economic-nexus thresholds (post-Wayfair HI adopted).",
            ],
            risks_and_caveats=[
                "HI GET audits aggressive; gross receipts definition is "
                "broader than federal gross income — includes reimbursements.",
                "County surcharge varies by island; Honolulu, Kauai, and "
                "Hawaii County rates differ.",
            ],
            cross_strategy_impacts=[
                "SSALT_SALES_USE_EXPOSURE",
                "SSALT_CONFORMITY_DECOUPLING",
                "SSALT_AUDIT_VDA",
            ],
            verification_confidence="medium",
        )
