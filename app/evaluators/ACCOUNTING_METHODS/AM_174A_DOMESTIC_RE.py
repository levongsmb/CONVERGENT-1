"""AM_174A_DOMESTIC_RE — OBBBA §174A domestic R&E current expensing.

OBBBA §70302 added IRC §174A, restoring current deductibility for
domestic research and experimental expenditures starting in tax year
2025. Foreign R&E remains under §174's 15-year amortization. The
§481(a) transition applies to amounts capitalized under the prior
§174 regime (2022-2024) — taxpayers can elect to accelerate the
unamortized balance into the transition year.

Applicable when: entity has R&D spending history or current projected
R&D spending, AND entity gross receipts qualify for the §448(c)
small-business exception OR entity elects to adopt §174A method.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "AM_174A_DOMESTIC_RE"
    CATEGORY_CODE = "ACCOUNTING_METHODS"
    PIN_CITES = [
        "IRC §174A as added by OBBBA §70302 — current expensing for domestic R&E",
        "IRC §174(a) — foreign R&E 15-year amortization (retained)",
        "IRC §481(a) — spread on method change",
        "IRC §280C — coordination with §41 research credit",
        "Rev. Proc. 2023-24 — automatic method change procedures (update anticipated)",
        "P.L. 119-21 §70302 — OBBBA §174A enactment",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        if year < 2025:
            return self._not_applicable(
                f"§174A effective TY 2025; scenario year {year} uses pre-OBBBA §174"
            )

        # Applicable when an operating entity exists (R&E spending
        # is typically at the entity level). Phase 3b adds a dedicated
        # research_expenditures field to Entity; MVP uses entity presence
        # as a flag.
        entities_with_possible_rd = [
            e for e in scenario.entities
            if e.type in (
                EntityType.S_CORP, EntityType.LLC_S_CORP,
                EntityType.C_CORP, EntityType.LLC_C_CORP,
                EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
            )
        ]
        if not entities_with_possible_rd:
            return self._not_applicable(
                "no operating entity in scenario; §174A applies at the "
                "entity level"
            )

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "entity's prior-year §174 capitalized balance (2022-2024 unamortized)",
                "current-year domestic vs foreign R&E breakdown",
                "§41 research credit posture (basis reduction under §280C(c))",
                "entity's §448(c) small-business exception status",
                "decision on §481(a) transition: accelerate vs spread",
            ],
            assumptions=[
                f"Entities potentially subject to §174A: {len(entities_with_possible_rd)}",
                "Foreign R&E continues to amortize over 15 years under §174.",
                "Domestic R&E current-expense election made via method change "
                "(Rev. Proc. 2023-24 successor).",
                "§280C(c)(1) elective reduction in §174A deduction by amount "
                "of §41 credit claimed (vs §280C(c)(2) basis reduction).",
            ],
            implementation_steps=[
                "Identify domestic vs foreign R&E spending per project; "
                "apply §174A to domestic only.",
                "File method change under automatic-consent procedures "
                "(Rev. Proc. 2023-24 or successor).",
                "§481(a) transition: choose between (a) accelerate "
                "unamortized §174 balance into 2025 or (b) continue "
                "amortizing the prior balance over remaining life. "
                "Acceleration aligns cash flow with new regime.",
                "Coordinate with §41 research credit and §280C election "
                "(basis reduction vs elective §280C(c)(2) reduction).",
                "For flow-through entities, the method change is filed at "
                "the entity level; K-1 allocations reflect the new treatment.",
            ],
            risks_and_caveats=[
                "Foreign R&E is expressly excluded from §174A; continues "
                "15-year amortization under §174. Misclassifying location "
                "of R&E is an audit target.",
                "§41 credit interaction: the §280C(c)(1) election reduces "
                "the §174A deduction by the §41 credit; many taxpayers prefer "
                "the §280C(c)(2) elective reduction of the credit to preserve "
                "the full §174A deduction.",
                "State conformity: CA and several other states have not "
                "conformed to §174A; state may still require capitalization.",
                "§481(a) unfavorable adjustments: spread over 4 years; "
                "favorable spread immediate.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "CR_RND_41",
                "RND_174A_DOMESTIC",
                "RND_174_FOREIGN_AMORT",
                "RND_280C_COORD",
                "AM_481A_PLANNING",
                "AM_448_GROSS_RECEIPTS",
            ],
            verification_confidence="high",
            computation_trace={
                "effective_year": 2025,
                "entities_potentially_affected": len(entities_with_possible_rd),
                "entity_codes": [e.code for e in entities_with_possible_rd],
            },
        )
