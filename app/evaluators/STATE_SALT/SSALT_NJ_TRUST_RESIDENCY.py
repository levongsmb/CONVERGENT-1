"""SSALT_NJ_TRUST_RESIDENCY — NJ trust residency determination."""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult
from app.scenario.models import ClientScenario, EntityType, StateCode


_TRUST_TYPES = {
    EntityType.TRUST_GRANTOR, EntityType.TRUST_NONGRANTOR,
    EntityType.TRUST_COMPLEX, EntityType.TRUST_SIMPLE,
}


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_NJ_TRUST_RESIDENCY"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "N.J.S.A. 54A:1-2(o) — NJ resident estate / trust definition",
        "Kassner v. Director, Division of Taxation, 211 N.J. 143 (2012) — "
        "due-process limit on NJ trust residency taxation",
        "Residuary Trust A v. Director, 27 N.J. Tax 68 (2013) — trust "
        "residency requires sufficient minimum contacts",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        trusts = [e for e in scenario.entities if e.type in _TRUST_TYPES]
        k1_trust = [
            k1 for k1 in scenario.income.k1_income
            if k1.entity_type in _TRUST_TYPES
        ]
        if not trusts and not k1_trust:
            return self._not_applicable(
                "no trust entities in scenario; NJ trust residency analysis "
                "requires a trust in the structure"
            )
        nj_nexus = any(
            t.formation_state == StateCode.NJ
            or StateCode.NJ in (t.operating_states or [])
            for t in trusts
        )
        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            pin_cites=list(self.PIN_CITES),
            inputs_required=[
                "trust formation state and governing law",
                "trustee residency and trustee location",
                "beneficiary residency",
                "trust assets located in NJ",
                "grantor residency (for NJ Kassner three-prong analysis)",
            ],
            assumptions=[
                "NJ statute defines a resident trust as one with an NJ-"
                "resident grantor OR NJ property OR NJ beneficiaries.",
                "Kassner held NJ cannot tax a nonresident-trustee, "
                "nonresident-beneficiary trust solely because grantor "
                "was NJ resident at creation — due-process limits apply.",
                "Residuary Trust A clarified that NJ must have ongoing "
                "minimum contacts to tax resident-trust worldwide income.",
            ],
            implementation_steps=[
                "Apply the Kassner three-prong test: trustee, beneficiary, "
                "trust property — if all are non-NJ, reject NJ residency.",
                "For trusts with only grantor-NJ connection, consider "
                "protective nonresident return + due-process defense.",
                "Document situs choices (trustee appointment, assets "
                "location) to support nonresident posture.",
                "Coordinate with SSALT_NJ_RESIDENT_CREDIT for beneficiary "
                "treatment.",
            ],
            risks_and_caveats=[
                "NJ continues to assert residency on grantor-connection trusts; "
                "litigation is the usual resolution.",
                "State-by-state grantor-trust rules vary; a trust NJ-resident "
                "at grant may be non-resident post-grant migration.",
            ],
            cross_strategy_impacts=[
                "SSALT_NJ_BAIT",
                "SSALT_NJ_RESIDENT_CREDIT",
                "EST_TRUST_SITUS",
                "EST_DING_NING_ING_TRUSTS",
            ],
            verification_confidence="medium",
            computation_trace={
                "trust_count": len(trusts),
                "trust_k1_count": len(k1_trust),
                "nj_nexus": nj_nexus,
            },
        )
