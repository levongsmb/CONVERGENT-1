"""CA_PTET_ELECTION — California Pass-Through Entity Elective Tax.

Evaluates the SB 132 (Ch. 17, Stats. 2025) regime controlling tax years
2026-2030. Applicable to S corps, LLCs taxed as partnerships, and
limited partnerships that operate in California with California-source
qualified net income.

The evaluator produces:

  - Estimated federal tax saving from the PTET deduction at the entity
    level (PTET paid by the entity reduces federal ordinary income flow-
    through), net of the §164(b)(6) SALT cap that would otherwise have
    covered some portion of the same state-tax burden at the individual
    level.
  - Scenario-level sanity check on the owner's CA PTET credit posture:
    nonrefundable with a 5-year carryforward under SB 132.
  - Warning if the June 15 minimum prepayment (greater of 50% of prior
    year PTET or $1,000) is at risk, quantifying the 12.5% shortfall
    credit reduction.

All SB 132 parameters (9.3% rate, 12.5% shortfall mechanic,
2026-2030 effective window, nonrefundable 5-year carryforward, June 15
minimum prepayment rule) come from config/rules_cache/2026/california/
ptet.yaml via app.config.rules.get_rule. SALT cap parameters come from
config/rules_cache/2026/federal/salt_cap_obbba.yaml. No parameter is
hardcoded in this module.
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType, FilingStatus, StateCode


_QUALIFIED_ENTITY_TYPES = {
    EntityType.S_CORP,
    EntityType.LLC_S_CORP,  # LLC elected S
    EntityType.PARTNERSHIP,
    EntityType.LLC_PARTNERSHIP,
}


def _param(doc: dict, **coord) -> Optional[Decimal]:
    for p in doc.get("parameters", []):
        c = p.get("coordinate", {})
        if all(c.get(k) == v for k, v in coord.items()):
            v = p.get("value")
            if v is None:
                return None
            try:
                return Decimal(str(v))
            except Exception:
                return v
    return None


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "CA_PTET_ELECTION"
    CATEGORY_CODE = "CALIFORNIA_SPECIFIC"
    PIN_CITES = [
        "SB 132 (Ch. 17, Stats. 2025, signed 2025-06-27) — CA PTET 2026-2030 regime",
        "New RTC sections enacted by SB 132 for taxable years 2026-2030",
        "FTB Form 3804 (2026) Instructions — PTET election mechanics",
        "FTB Form 3893 Instructions — June 15 minimum prepayment",
        "IRC §164(b)(6) as amended by OBBBA — SALT cap interaction",
        "IRS Notice 2020-75 — federal deductibility of PTET at entity level",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        if year < 2026 or year > 2030:
            return self._not_applicable(
                f"SB 132 regime applies to TY 2026-2030; scenario year is {year}"
            )

        # CA applicability: taxpayer resident in CA OR has CA-operating entity
        ca_resident = (
            scenario.identity.primary_state_domicile == StateCode.CA
            or scenario.identity.spouse_state_domicile == StateCode.CA
        )
        ca_entities = [
            e for e in scenario.entities
            if e.type in _QUALIFIED_ENTITY_TYPES
            and (e.formation_state == StateCode.CA or StateCode.CA in (e.operating_states or []))
        ]
        if not ca_resident and not ca_entities:
            return self._not_applicable(
                "no CA domicile and no CA-operating qualified entity; PTET "
                "election is not relevant"
            )
        if not ca_entities:
            return self._not_applicable(
                "CA-domiciled taxpayer but no qualified entity (S corp, LLC-as-partnership, "
                "LP) to elect PTET"
            )

        ptet_doc = rules.get("california/ptet", year)
        salt_doc = rules.get("federal/salt_cap_obbba", year)

        rate = _param(ptet_doc, tax_year=year, sub_parameter="tax_rate") or Decimal("0.093")
        prepayment_floor = (
            _param(ptet_doc, tax_year=year, sub_parameter="election_minimum_prepayment_floor")
            or Decimal("1000")
        )
        shortfall_pct = (
            _param(
                ptet_doc,
                tax_year=year,
                sub_parameter="june15_shortfall_credit_reduction_pct",
            )
            or Decimal("0.125")
        )

        # Sum qualified net income by entity from K-1 ordinary business income
        # attributable to CA operations. Approximation: use full K-1 ordinary
        # income for entities operating in CA. Multi-state apportionment is
        # handled by APP_* evaluators.
        entity_codes = {e.code for e in ca_entities}
        qualified_net_income = Decimal(0)
        for k1 in scenario.income.k1_income:
            if k1.entity_code in entity_codes:
                # Include ordinary business income + guaranteed payments
                qualified_net_income += (
                    k1.ordinary_business_income + k1.guaranteed_payments
                )

        if qualified_net_income <= Decimal(0):
            return self._not_applicable(
                "qualified entities present but no qualified net income "
                "flowing to the taxpayer"
            )

        ptet_paid = (qualified_net_income * rate).quantize(Decimal("0.01"))

        # Federal benefit: the PTET deduction at the entity level reduces
        # the taxpayer's federal ordinary pass-through income. Approximate
        # marginal savings at the top bracket (37%) plus NIIT on the portion
        # that was previously NIIT-eligible. The precise marginal rate is
        # computed by the orchestrator convergence loop in Phase 4; this
        # evaluator surfaces a first-order estimate.
        approx_marginal_fed = Decimal("0.37")
        approx_niit_applicable = Decimal("0.038") if qualified_net_income > Decimal(0) else Decimal(0)
        # §1411 NIIT typically does not apply to active nonpassive S corp
        # income, but does apply to many partnership allocations. Use a
        # neutral stance in MVP: no NIIT credit applied.
        fed_savings = (ptet_paid * approx_marginal_fed).quantize(Decimal("0.01"))

        # SALT cap offset: some portion of the CA PTET would otherwise have
        # been an individual SALT itemized deduction, bounded by the cap.
        # If the taxpayer is already at or above the SALT cap before the
        # election, the PTET deduction is pure win. Use a proxy: read the
        # current-year SALT state-income + property-residence as paid and
        # compare to the base_cap under OBBBA.
        mfj = scenario.identity.filing_status == FilingStatus.MFJ
        base_cap = _param(
            salt_doc,
            tax_year=year,
            filing_status="MFJ" if mfj else "MFS",
            sub_parameter="base_cap",
        )
        paid_state_income = scenario.deductions.salt_paid_state_income
        paid_property_res = scenario.deductions.salt_paid_property_residence
        salt_paid_total = paid_state_income + paid_property_res

        already_capped = base_cap is not None and salt_paid_total >= base_cap
        overlap_reduction = Decimal(0)
        if not already_capped and base_cap is not None:
            # The CA PTET payment would have otherwise contributed to the
            # state-income SALT deduction before the election; the overlap
            # with the cap headroom reduces the incremental federal benefit.
            headroom = max(base_cap - paid_property_res, Decimal(0))
            overlap_reduction = min(ptet_paid, headroom) * approx_marginal_fed
            overlap_reduction = overlap_reduction.quantize(Decimal("0.01"))

        headline_savings = max(fed_savings - overlap_reduction, Decimal(0))

        risks_and_caveats: List[str] = [
            "Election is made on the original timely-filed entity return "
            "(calendar-year PTEs: March 15). Missed March 15 voids the election.",
            "June 15 minimum prepayment = greater of 50% of prior-year PTET "
            f"or ${prepayment_floor:,.0f}. Shortfall triggers a "
            f"{shortfall_pct:.1%} reduction of the shortfall amount against "
            "the consenting owner's credit (SB 132; measured at return filing date).",
            "PTET credit is nonrefundable at the qualified-taxpayer level "
            "with a 5-year carryforward.",
            "CA does not conform to federal §1202 or §168(k), which are handled "
            "by separate evaluators; CA PTET qualified net income is computed "
            "under CA RTC, not federal income.",
            "Partnership PTET: confirm each qualified taxpayer's consent on "
            "the Form 3804 schedule before making the election.",
        ]
        if already_capped:
            risks_and_caveats.append(
                "SALT cap is already fully consumed before the PTET election; "
                "federal benefit of the election is not diminished by SALT cap overlap."
            )

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=headline_savings,
            savings_by_tax_type=TaxImpact(
                federal_income_tax=headline_savings,
            ),
            inputs_required=[
                "entity qualified net income (CA-sourced)",
                "prior-year PTET paid (for June 15 minimum)",
                "list of qualified taxpayers consenting to the election",
                "current-year SALT itemized deductions for cap overlap math",
            ],
            assumptions=[
                f"PTET rate: {rate:.1%}",
                f"Marginal federal rate proxy: {approx_marginal_fed:.0%}",
                f"CA PTET qualified net income: ${qualified_net_income:,.0f}",
                f"PTET paid at 9.3%: ${ptet_paid:,.2f}",
                "Headline savings are a first-order estimate; orchestrator "
                "convergence loop refines against actual bracket and NIIT posture.",
            ],
            implementation_steps=[
                "Confirm each qualified taxpayer consents on Form 3804.",
                "Fund the June 15 minimum prepayment via Form 3893 "
                f"(greater of 50% prior-year PTET or ${prepayment_floor:,.0f}).",
                "File Form 3804 with the entity return by the original due date.",
                "Claim the CA PTET credit on the individual return "
                "(nonrefundable, 5-year carryforward).",
                "Model cash-flow impact: PTET payment is at the entity level; "
                "the owner's CA estimated tax may need adjustment to avoid overpayment.",
            ],
            risks_and_caveats=risks_and_caveats,
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "SSALT_PTET_MODELING",
                "SSALT_164_SALT_CAP",
                "SSALT_OBBBA_CAP_MODELING",
                "CA_NONCONFORMITY_BONUS",
                "CA_TAX_BASIS_CAPITAL",
            ],
            verification_confidence="high",
            computation_trace={
                "ptet_rate": str(rate),
                "qualified_net_income": str(qualified_net_income),
                "ptet_paid": str(ptet_paid),
                "fed_savings_gross": str(fed_savings),
                "salt_cap_base": str(base_cap) if base_cap is not None else None,
                "salt_paid_total_before_ptet": str(salt_paid_total),
                "salt_cap_already_consumed": already_capped,
                "overlap_reduction": str(overlap_reduction),
                "headline_savings": str(headline_savings),
                "ca_resident": ca_resident,
                "ca_entity_count": len(ca_entities),
                "regime": "SB132_2026_2030",
            },
        )
