"""SET_1402A13 — §1402(a)(13) limited partner SE exception.

§1402(a)(13) excludes a limited partner's distributive share of
partnership income from net earnings from SE, with a carve-out for
guaranteed payments for services. The Tax Court's decisions in
Soroban (2023), Denham, and Point 72 established that the exception
applies in substance and not in form — an LLC member who actively
participates can be treated as a general partner for §1402 purposes.

Applicable when taxpayer has an LLC-as-partnership K-1 and may have
claimed the exception or needs to evaluate exposure.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SET_1402A13"
    CATEGORY_CODE = "SELF_EMPLOYMENT_TAX"
    PIN_CITES = [
        "IRC §1402(a)(13) — limited partner exception",
        "Soroban Capital Partners LP v. Commissioner, 161 T.C. No. 12 (2023)",
        "Denham Capital Management LP v. Commissioner (Tax Court 2024)",
        "Point 72 Asset Management, LP v. Commissioner (Tax Court 2024)",
        "Prop. Treas. Reg. §1.1402(a)-2 (1997) — never finalized",
        "Castigliola v. Commissioner, T.C. Memo 2017-62 — active LLC member",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        partnership_k1s = [
            k1 for k1 in scenario.income.k1_income
            if k1.entity_type in (
                EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP
            )
        ]
        if not partnership_k1s:
            return self._not_applicable(
                "no partnership K-1 in scenario; §1402(a)(13) exception is "
                "partnership-specific"
            )

        findings: list = []
        for k1 in partnership_k1s:
            has_guaranteed_payments = k1.guaranteed_payments > Decimal(0)
            has_se_earnings_reported = k1.self_employment_earnings > Decimal(0)
            full_distributive = k1.ordinary_business_income + k1.guaranteed_payments
            # Exception appears claimed when SE earnings reported are less
            # than the full distributive share — partial or total exclusion
            # of ordinary business income from SE income.
            exception_claimed = (
                k1.ordinary_business_income > Decimal(0)
                and k1.self_employment_earnings < full_distributive
            )
            full_distributive_se = (
                k1.self_employment_earnings >= full_distributive
                and full_distributive > Decimal(0)
            )
            findings.append({
                "entity_code": k1.entity_code,
                "ordinary_business_income": str(k1.ordinary_business_income),
                "guaranteed_payments": str(k1.guaranteed_payments),
                "self_employment_earnings_reported": str(k1.self_employment_earnings),
                "has_guaranteed_payments": has_guaranteed_payments,
                "exception_likely_claimed": exception_claimed,
                "full_distributive_share_treated_as_se": full_distributive_se,
            })

        risk_posture: list = []
        any_exception = any(f["exception_likely_claimed"] for f in findings)
        any_full_se = any(f["full_distributive_share_treated_as_se"] for f in findings)
        if any_exception:
            risk_posture.append("HIGH_RISK")
        if any_full_se:
            risk_posture.append("SOROBAN_CONSERVATIVE")

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "LLC operating agreement — member vs manager structure",
                "hours per year devoted by member (Soroban functional test)",
                "authority / control / profit-sharing terms",
                "written evidence of passive vs active role (emails, minutes)",
                "prior-year §1402 reporting posture per K-1",
            ],
            assumptions=[
                f"Partnership K-1 positions evaluated: {len(findings)}",
                f"Risk posture: {', '.join(risk_posture) if risk_posture else 'LOW'}",
                "Soroban framework: functional test (time, authority, "
                "management) NOT nominal 'limited partner' label controls.",
                "Exception survives for passive investors; fails for active "
                "members akin to general partners.",
            ],
            implementation_steps=[
                "Review Soroban / Denham / Point 72 functional factors for "
                "each LLC member invoking the exception.",
                "For active members: report FULL distributive share as SE "
                "earnings (conservative) OR disclose the position on Form "
                "8275 with reasonable-basis documentation.",
                "Rework LLC structure: if the exception is material, "
                "consider a bona fide limited-partner class for the passive "
                "member pool (with non-managerial, no-day-to-day authority).",
                "Coordinate with ENT_LLC_PSHIP_VS_SCORP: flipping to S corp "
                "eliminates the §1402 question entirely.",
            ],
            risks_and_caveats=[
                "Soroban / Point 72 / Denham establish that the IRS and Tax "
                "Court apply a functional test. Claiming the exception for "
                "an active member is high-risk and likely to be challenged.",
                "Guaranteed payments for services remain SE-taxable even if "
                "the exception applies to distributive share.",
                "SECA-based retirement (Solo 401(k) for SE members) requires "
                "SE earnings — taking the §1402(a)(13) exception may block "
                "retirement plan eligibility.",
                "§1411 NIIT interaction: income that is NOT SE earnings and "
                "IS NOT nonpassive trade-or-business income may fall into "
                "NII, subject to 3.8%.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "SET_SCORP_CONVERSION",
                "SET_SOROBAN_RISK",
                "SET_LIMITED_PARTNER_EXCEPT",
                "ENT_LLC_PSHIP_VS_SCORP",
                "NIIT_MATERIAL_PARTIC",
                "NIIT_BUSINESS_VS_INVEST",
                "RET_SOLO_401K",
            ],
            verification_confidence="medium",
            computation_trace={
                "partnership_k1_count": len(partnership_k1s),
                "findings": findings,
                "any_exception_claimed": any_exception,
                "any_full_distributive_se": any_full_se,
                "risk_posture": risk_posture,
            },
        )
