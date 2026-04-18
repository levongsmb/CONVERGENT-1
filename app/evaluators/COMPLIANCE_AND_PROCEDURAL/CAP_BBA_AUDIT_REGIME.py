"""CAP_BBA_AUDIT_REGIME — BBA partnership audit regime procedural elections."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CAP_BBA_AUDIT_REGIME"
    CATEGORY_CODE = "COMPLIANCE_AND_PROCEDURAL"
    PIN_CITES = [
        "IRC §6221 through §6241 — Bipartisan Budget Act partnership audit regime",
        "IRC §6221(b) — election out for small partnerships (≤100 partners, eligible partner types)",
        "IRC §6223 — partnership representative",
        "IRC §6226 — push-out election",
        "IRC §6227 — administrative adjustment request (AAR)",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        partnerships = [
            e for e in scenario.entities
            if e.type in (EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP)
        ]
        if not partnerships:
            return self._not_applicable(
                "no partnership in scenario; BBA regime is partnership-specific"
            )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "partner count and partner types (must be eligible for §6221(b))",
                "partnership representative identity and designated individual",
                "prior-year §6221(b) election-out posture",
                "AAR and push-out-election history",
            ],
            assumptions=[
                "§6221(b) election-out: partnerships ≤100 partners consisting "
                "of only eligible partners (individuals, C corps, S corps, "
                "estates, certain trusts) may elect out annually.",
                "Default BBA regime imposes entity-level imputed underpayment "
                "unless §6226 push-out elected within 45 days of FPAA.",
            ],
            implementation_steps=[
                "Test §6221(b) eligibility: count partners by type. LLC-member "
                "or disregarded-entity partner blocks election.",
                "Designate partnership representative (§6223) — specific "
                "individual with substantial US presence.",
                "If election-out preferred: attach Election-Out Statement to "
                "timely-filed Form 1065.",
                "On audit adjustment: evaluate §6226 push-out vs entity-level "
                "imputed underpayment within 45 days.",
            ],
            risks_and_caveats=[
                "LLC-partner blocks §6221(b) election-out entirely — even a "
                "single-member LLC partner disqualifies the election.",
                "Partnership representative has binding authority over all "
                "partners; select carefully and document succession.",
                "Imputed underpayment is computed at highest marginal rate "
                "unless modified — modification requires partner-level "
                "amended returns and information.",
            ],
            cross_strategy_impacts=[
                "CAP_PUSH_OUT_ELECTION",
                "CAP_PR_CONTROLS",
                "CAP_EXAMS_APPEALS",
                "PS_LAYERING",
            ],
            verification_confidence="high",
        )
