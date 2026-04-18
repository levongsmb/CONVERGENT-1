"""CR_RND_41 — §41 research credit.

The §41 credit rewards qualified research expenses (QREs) — generally
a regular credit of 20% of the excess of current QREs over a base amount
or an alternative simplified credit (ASC) of 14% of current QREs over
50% of the prior 3-year average QRE. For startups under §41(h),
the credit offsets up to $500,000 of §3111(a) OASDI payroll tax.

Coordinates with §174A current expensing (AM_174A_DOMESTIC_RE) and
§280C basis-reduction election.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


_STARTUP_PAYROLL_OFFSET_CAP = Decimal("500000")
_STARTUP_REVENUE_CEILING = Decimal("5000000")


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CR_RND_41"
    CATEGORY_CODE = "CREDITS"
    PIN_CITES = [
        "IRC §41(a) — research credit structure",
        "IRC §41(b) — qualified research expenses (wages, supplies, contract research)",
        "IRC §41(c)(4) — alternative simplified credit 14% method",
        "IRC §41(d) — qualified research definition (4-part test)",
        "IRC §41(h) — startup payroll-tax offset up to $500K",
        "IRC §280C(c) — coordination with §174A domestic R&E expensing",
        "Treas. Reg. §1.41-4 — qualified research rules",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        ops = [
            e for e in scenario.entities
            if e.type in (
                EntityType.S_CORP, EntityType.LLC_S_CORP,
                EntityType.C_CORP, EntityType.LLC_C_CORP,
                EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
            )
        ]
        if not ops:
            return self._not_applicable(
                "no operating entity; §41 credit applies at the entity level"
            )

        # Identify startup-eligible entities: gross receipts < $5M for the
        # current taxable year AND no gross receipts for any taxable year
        # preceding the 5-tax-year period ending with the current year.
        # MVP proxy: current-year gross receipts < $5M.
        startup_candidates: list = []
        regular_candidates: list = []
        for e in ops:
            gross = e.gross_receipts_prior_year or e.gross_receipts_prior_3_avg
            if gross is None:
                continue
            record = {
                "entity_code": e.code,
                "entity_type": e.type.value,
                "gross_receipts_proxy": str(gross),
            }
            if gross < _STARTUP_REVENUE_CEILING:
                startup_candidates.append(record)
            else:
                regular_candidates.append(record)

        if not startup_candidates and not regular_candidates:
            return self._not_applicable(
                "no entity with gross-receipts data to classify §41 eligibility"
            )

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),  # credit size depends on QRE, not yet in schema
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "qualified research expense (QRE) detail: wages, supplies, contract research, cloud/computer rental",
                "prior three-year QRE history for ASC base amount",
                "§280C(c)(1) or §280C(c)(2) election decision",
                "four-part test documentation per research project "
                "(qualified purpose, technological uncertainty, process of "
                "experimentation, qualified research)",
                "payroll tax base for §41(h) offset eligibility (if startup)",
            ],
            assumptions=[
                f"Entities on §41 startup-offset track (< $5M gross): "
                f"{len(startup_candidates)}",
                f"Entities on regular §41 track: {len(regular_candidates)}",
                f"Startup payroll-offset cap: ${_STARTUP_PAYROLL_OFFSET_CAP:,.0f}",
                "ASC method: 14% of current QRE > 50% of prior 3-year "
                "average QRE. Usually selected when prior-year base is "
                "unfavorable or unknown.",
                "§280C(c)(2) election reduces the §41 credit by the 21% "
                "corporate rate equivalent to preserve full §174A deduction; "
                "§280C(c)(1) default reduces §174A deduction by the credit.",
            ],
            implementation_steps=[
                "Commission a §41 study per QRE period — typically "
                "third-party specialist firm.",
                "Document the four-part test per research project.",
                "For startups: elect §41(h) payroll-tax offset on Form 6765 "
                "Section D; file Form 8974 quarterly.",
                "For regular: elect §280C(c)(2) on Form 6765 to reduce the "
                "credit (preserves §174A deduction).",
                "Coordinate with AM_174A_DOMESTIC_RE and RND_280C_COORD for "
                "the §174A interaction.",
                "Retain contemporaneous time tracking and project "
                "documentation; IRS audit scrutiny is elevated for §41.",
            ],
            risks_and_caveats=[
                "§41 has been audited aggressively since 2024 with the Form "
                "6765 overhaul (2025+ requires project-level detail). "
                "Maintain contemporaneous records.",
                "Qualified research excludes social-science research, "
                "market research, research conducted outside the United "
                "States, and research funded by grants or government "
                "contracts.",
                "ASC vs Regular credit: ASC is simpler but produces a smaller "
                "credit when prior-year QRE history is sparse. Rerun the "
                "comparison annually.",
                "Startup §41(h) offset is claimed against FICA not federal "
                "income tax. Flow-through entities pass through the offset "
                "per §41(h)(4).",
                "State R&D credit piggybacks: CA, NY, MA have separate "
                "credits. Do NOT assume state conformity.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "AM_174A_DOMESTIC_RE",
                "RND_174A_DOMESTIC",
                "RND_280C_COORD",
                "RND_41_QUALIFICATION",
                "CR_STARTUP_PAYROLL_OFFSET",
                "CR_ORDERING_LIMITS",
                "AM_481A_PLANNING",
            ],
            verification_confidence="high",
            computation_trace={
                "startup_track_entities": startup_candidates,
                "regular_track_entities": regular_candidates,
                "startup_payroll_offset_cap": str(_STARTUP_PAYROLL_OFFSET_CAP),
                "startup_revenue_ceiling": str(_STARTUP_REVENUE_CEILING),
            },
        )
