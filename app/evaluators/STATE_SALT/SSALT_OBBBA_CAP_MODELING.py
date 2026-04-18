"""SSALT_OBBBA_CAP_MODELING — §164(b)(6) SALT cap under OBBBA with
phaseout and 2030 reversion.

Computes the effective SALT deduction after OBBBA phaseout. Flags
planning opportunities to bunch SALT payments into high-cap years or
compress MAGI under the phaseout threshold.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, FilingStatus


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


def _approx_magi(scenario: ClientScenario) -> Decimal:
    income = scenario.income
    base = (
        income.wages_primary
        + income.wages_spouse
        + income.self_employment_income
        + income.interest_ordinary
        + income.dividends_ordinary
        + income.dividends_qualified
        + income.capital_gains_long_term
        + income.capital_gains_short_term
        + income.rental_income_net
    )
    for k1 in income.k1_income:
        base += (
            k1.ordinary_business_income
            + k1.interest_income
            + k1.dividend_income
            + k1.capital_gain_long_term
            + k1.capital_gain_short_term
            + k1.guaranteed_payments
        )
    return base


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "SSALT_OBBBA_CAP_MODELING"
    CATEGORY_CODE = "STATE_SALT"
    PIN_CITES = [
        "IRC §164(b)(6)(B) as amended by OBBBA — base cap schedule 2025-2029",
        "IRC §164(b)(6)(C) as amended by OBBBA — 30% phaseout of MAGI excess",
        "IRC §164(b)(6)(D) as amended by OBBBA — $10K / $5K MFS floor",
        "IRC §164(b)(6)(E) — 2030 sunset reversion",
        "P.L. 119-21 — OBBBA SALT cap amendments",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        deductions = scenario.deductions
        salt_paid = (
            deductions.salt_paid_state_income
            + deductions.salt_paid_property_residence
            + deductions.salt_paid_sales_tax
        )
        if salt_paid <= Decimal(0):
            return self._not_applicable(
                "no SALT payments (state income, property, sales) in scenario"
            )

        salt = rules.get("federal/salt_cap_obbba", year)
        filing_status = scenario.identity.filing_status
        fs_key = "MFS" if filing_status == FilingStatus.MFS else "MFJ"

        base_cap = _param(salt, tax_year=year, filing_status=fs_key, sub_parameter="base_cap")
        threshold = _param(
            salt, tax_year=year, filing_status=fs_key, sub_parameter="phaseout_magi_threshold"
        )
        phaseout_rate = _param(salt, sub_parameter="phaseout_rate") or Decimal("0.30")
        floor = _param(salt, filing_status=fs_key, sub_parameter="floor")

        if base_cap is None or floor is None:
            return StrategyResult(
                subcategory_code=self.SUBCATEGORY_CODE,
                applicable=True,
                reason=f"SALT cap parameters for {year}/{fs_key} incomplete in rules cache",
                pin_cites=list(self.PIN_CITES),
                verification_confidence="low",
                computation_trace={"year": year, "filing_status": fs_key},
            )

        magi = _approx_magi(scenario)
        phaseout_reduction = Decimal(0)
        if threshold is not None and magi > threshold:
            phaseout_reduction = (magi - threshold) * phaseout_rate
        effective_cap = max(base_cap - phaseout_reduction, floor)
        salt_above_cap = max(salt_paid - effective_cap, Decimal(0))

        # Marginal-rate proxy (orchestrator refines downstream)
        approx_marginal = Decimal("0.32")
        disallowed_tax_cost = (salt_above_cap * approx_marginal).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),  # surfaces loss posture, not dollar save
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "SALT paid: state income, property residence, property personal-use, sales",
                "current-year MAGI (for phaseout)",
                "projected prior-year SALT for bunching modeling",
            ],
            assumptions=[
                f"Base cap for {year} ({fs_key}): ${base_cap:,.0f}",
                f"Phaseout threshold: ${threshold:,.0f}" if threshold else "No phaseout threshold",
                f"Phaseout rate: {phaseout_rate:.0%}",
                f"Floor: ${floor:,.0f}",
                f"Approx MAGI: ${magi:,.0f}",
                f"Effective cap after phaseout: ${effective_cap:,.0f}",
            ],
            implementation_steps=[
                "Pair with CA_PTET_ELECTION or other PTET election to shift "
                "state income tax below the individual SALT cap.",
                "Model multi-year bunching: accelerate SALT into years with "
                "higher effective cap, defer into low-cap years.",
                "If MAGI is near the phaseout threshold, evaluate compression "
                "strategies (retirement deferrals, charitable bunching) to "
                "preserve higher effective cap.",
            ],
            risks_and_caveats=[
                "OBBBA cap reverts to $10K/$5K floor in 2030; multi-year plans "
                "crossing the sunset must model the cliff.",
                "Property tax on investment-use property is not subject to the "
                "§164(b)(6) cap; verify classification before including.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "CA_PTET_ELECTION",
                "SSALT_PTET_MODELING",
                "SSALT_PROPERTY_TAX_TIMING",
                "CHAR_BUNCHING",
                "QBI_INCOME_COMPRESSION",
            ],
            verification_confidence="high",
            computation_trace={
                "salt_paid": str(salt_paid),
                "base_cap": str(base_cap),
                "magi": str(magi),
                "phaseout_reduction": str(phaseout_reduction),
                "effective_cap": str(effective_cap),
                "salt_above_cap": str(salt_above_cap),
                "disallowed_tax_cost_at_proxy_rate": str(disallowed_tax_cost),
                "filing_status": fs_key,
            },
        )
