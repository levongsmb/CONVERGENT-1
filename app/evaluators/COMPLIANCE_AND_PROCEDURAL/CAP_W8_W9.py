"""CAP_W8_W9 — W-8 and W-9 collection and substantiation."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_W8_W9"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §1441 — withholding on payments to nonresident aliens",
        "IRC §1442 — withholding on payments to foreign corporations",
        "IRC §1471 through §1474 — FATCA (Ch. 4)",
        "Treas. Reg. §1.1441-1 — documentation requirements",
        "Form W-9, W-8BEN, W-8BEN-E, W-8IMY, W-8EXP, W-8ECI instructions",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        operating = [
            e for e in scenario.entities
            if e.type != EntityType.TRUST_GRANTOR
        ]
        if not operating:
            return self._not_applicable(
                "no payor entity; W-8 / W-9 collection is payor-side"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "current vendor W-9 / W-8 on file (expired W-8s trigger presumption rules)",
                "payment type (effectively connected income, FDAP, etc.)",
                "treaty claim status per foreign vendor",
                "qualified intermediary / withholding foreign partnership designations",
            ],
            assumptions=[
                "W-9 from US payees: required to avoid backup withholding.",
                "W-8BEN (individual) / W-8BEN-E (entity): 3-year validity "
                "unless change in circumstance.",
                "Missing or defective W-8 → presumption rules (§1.1441-1(b)) "
                "treat payee as foreign at 30% (or lower treaty rate with "
                "proper documentation).",
                "FATCA Ch. 4: additional 30% withholding on FDAP and certain "
                "gross proceeds for non-participating FFIs.",
            ],
            implementation_steps=[
                "Collect Form W-9 from every US vendor or customer before "
                "first payment.",
                "Collect Form W-8BEN / W-8BEN-E from foreign vendors; validate "
                "treaty country and LOB article compliance.",
                "Track W-8 expiration calendar (generally 3 years).",
                "On presumption-rule triggers: withhold at 30% (or 24% "
                "backup) until cured.",
                "File Form 1042 and 1042-S for withholding on foreign payees.",
            ],
            risks_and_caveats=[
                "Treaty benefits require (a) valid W-8BEN / BEN-E, (b) LOB "
                "article eligibility, (c) beneficial ownership. Defective on "
                "any element → full 30% withholding.",
                "FATCA and Ch. 3 withholding operate in parallel; generally "
                "withhold once at the greater rate.",
            ],
            cross_strategy_impacts=[
                "CAP_1099",
                "CAP_BACKUP_WITHHOLDING",
                "II_FDAP",
                "II_1441_1442",
                "II_TREATY_BENEFITS",
            ],
            verification_confidence="high",
        )
