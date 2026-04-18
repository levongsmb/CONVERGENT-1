"""LL_163J_INTEREST — business interest limitation under §163(j).

OBBBA restored EBITDA-based ATI for §163(j) starting 2025, replacing
the EBIT-only calculation. Also preserves the §448(c) small-business
exemption (gross receipts test) and the real-property-trade election-out
under §163(j)(7)(B).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "LL_163J_INTEREST"
    CATEGORY_CODE = "LOSS_LIMIT_NAVIGATION"
    PIN_CITES = [
        "IRC §163(j) — business interest limitation",
        "IRC §163(j)(8) — ATI definition with OBBBA EBITDA restoration",
        "IRC §163(j)(3) — small business exception under §448(c) gross receipts test",
        "IRC §163(j)(7)(B) — electing real property trade or business",
        "OBBBA — EBITDA-based ATI restoration effective TY 2025",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        # Applicability: any scenario with an entity whose prior-year average
        # gross receipts exceed the §448(c) threshold (subject to
        # aggregation). Or any entity with §163(j) carryover.
        relevant_entities = [
            e for e in scenario.entities
            if (
                (e.gross_receipts_prior_3_avg is not None
                 and e.gross_receipts_prior_3_avg > Decimal("25000000"))
                or (e.gross_receipts_prior_year is not None
                    and e.gross_receipts_prior_year > Decimal("25000000"))
            )
        ]
        has_carryover = scenario.prior_year.suspended_163j_carryover > Decimal(0)

        if not relevant_entities and not has_carryover:
            return self._not_applicable(
                "no entity above §448(c) gross-receipts exemption and no §163(j) carryover"
            )

        # Note: the $25M tested here is a placeholder — the exact §448(c)
        # threshold for the planning year is config-sourced when the
        # accounting_methods file is populated in a later pass. Evaluator
        # flags the applicable-but-confirm posture.

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "entity business interest expense",
                "entity adjusted taxable income (ATI) under OBBBA EBITDA method",
                "§448(c) gross receipts — prior three-year average (indexed)",
                "§163(j) carryover by entity from prior years",
                "real-property trade or business election-out posture",
            ],
            assumptions=[
                f"Entities with gross receipts proxy above $25M: {len(relevant_entities)}",
                f"Prior §163(j) carryover: ${scenario.prior_year.suspended_163j_carryover:,.2f}",
                "OBBBA EBITDA-based ATI applies for TY 2025 onward.",
            ],
            implementation_steps=[
                "Confirm each entity's §448(c) gross-receipts exemption "
                "status at the planning year's indexed threshold.",
                "For entities above the threshold, compute ATI under "
                "OBBBA's EBITDA-based method and apply the 30% cap.",
                "Evaluate the §163(j)(7)(B) real-property trade election "
                "where disallowed interest would otherwise accrue; the "
                "election switches the electing activity to ADS depreciation.",
                "Track prior-year §163(j) carryover per entity; carryover "
                "has no time limit under §163(j)(2).",
            ],
            risks_and_caveats=[
                "The §163(j)(7)(B) real-property election is IRREVOCABLE. "
                "Pair with RED_163J_REPTOB before making the election.",
                "Aggregation under §448(c)(2) combines related entities for "
                "the gross-receipts test. Verify the control-group posture.",
                "The OBBBA EBITDA restoration applies at the entity level; "
                "individual owner interest deductions flow through per "
                "§163(j)(4) at the partner / shareholder level.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "RED_163J_REPTOB",
                "AM_448_GROSS_RECEIPTS",
                "LL_163J_EBITDA_OBBBA",
                "LL_NOL_USAGE",
            ],
            verification_confidence="high",
            computation_trace={
                "relevant_entity_count": len(relevant_entities),
                "prior_163j_carryover": str(scenario.prior_year.suspended_163j_carryover),
                "has_carryover": has_carryover,
            },
        )
