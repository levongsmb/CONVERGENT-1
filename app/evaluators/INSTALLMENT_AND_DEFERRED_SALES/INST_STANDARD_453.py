"""INST_STANDARD_453 — standard §453 installment sale.

When a planned sale has seller financing (note, earnout, deferred
payment), §453 reports gain ratably as payments are received. The
seller defers tax on the unreceived portion but remains exposed to
§453A interest on installment receivables > $5M.

The evaluator identifies the deferral opportunity, quantifies the NPV
saving at discount rate, and flags §453A exposure, §453(e) related-
party second-disposition risk, pledge-rule under §453A(d), and
recapture-acceleration under §453(i).
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


_453A_THRESHOLD = Decimal("5000000")  # §453A(b) threshold
_DISCOUNT_RATE = Decimal("0.07")  # assumed time-value-of-money on deferred tax
_DEFAULT_INSTALLMENT_YEARS = 5


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "INST_STANDARD_453"
    CATEGORY_CODE = "INSTALLMENT_AND_DEFERRED_SALES"
    PIN_CITES = [
        "IRC §453 — installment method",
        "IRC §453(d) — election out of installment method",
        "IRC §453(e) — related-party second disposition",
        "IRC §453(i) — recapture income recognized in year of sale",
        "IRC §453A — interest on deferred installment receivables > $5M",
        "IRC §453A(d) — pledge rule",
        "Rev. Rul. 69-462 — installment sale timing",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        liquidity = scenario.planning.liquidity_event_planned
        if liquidity is None:
            return self._not_applicable(
                "no liquidity event planned; §453 installment analysis requires "
                "a planned sale"
            )

        proceeds_raw = liquidity.get("expected_proceeds")
        if proceeds_raw is None:
            return self._not_applicable(
                "liquidity_event_planned lacks expected_proceeds"
            )
        proceeds = Decimal(str(proceeds_raw))

        # Target entity for basis estimate
        targets = [
            e for e in scenario.entities
            if e.type in (
                EntityType.S_CORP, EntityType.LLC_S_CORP,
                EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
                EntityType.C_CORP, EntityType.LLC_C_CORP,
            )
        ]
        seller_basis = Decimal(0)
        target_code = None
        if targets:
            t = targets[0]
            seller_basis = t.stock_basis or t.outside_basis or Decimal(0)
            target_code = t.code

        gross_gain = max(proceeds - seller_basis, Decimal(0))
        if gross_gain <= Decimal(0):
            return self._not_applicable(
                "no gain anticipated on planned sale; §453 deferral adds no value"
            )

        # Assume an earnout / deferred portion per scenario hint, default 20%
        deferred_pct = Decimal(str(liquidity.get("earnout_component_pct", 20))) / Decimal(100)
        if deferred_pct <= Decimal(0):
            return self._not_applicable(
                "no earnout or deferred-payment component; standard §453 does "
                "not apply to all-cash closings (unless seller note extends)"
            )

        deferred_principal = (proceeds * deferred_pct).quantize(Decimal("0.01"))
        deferred_gain = (gross_gain * deferred_pct).quantize(Decimal("0.01"))
        cap_gain_rate = Decimal("0.238")
        deferred_tax = (deferred_gain * cap_gain_rate).quantize(Decimal("0.01"))

        # NPV benefit at assumed discount rate over default installment years
        # Simplified: deferred_tax × (1 − 1/(1+r)^n) / (n × r) effectively
        # calculates the NPV saving vs. paying all tax at close. Use a direct
        # spreading approximation: present value of tax paid ratably over
        # n years.
        n = _DEFAULT_INSTALLMENT_YEARS
        pv_factor = Decimal(0)
        for t_yr in range(1, n + 1):
            pv_factor += Decimal(1) / ((Decimal(1) + _DISCOUNT_RATE) ** t_yr)
        pv_of_ratable_tax = (deferred_tax / Decimal(n) * pv_factor).quantize(Decimal("0.01"))
        npv_benefit = (deferred_tax - pv_of_ratable_tax).quantize(Decimal("0.01"))

        # §453A interest exposure
        a_453_exposure = deferred_principal > _453A_THRESHOLD
        a_453_interest_proxy = Decimal(0)
        if a_453_exposure:
            # §453A(c) interest ≈ deferred tax × AFR × (deferred principal
            # over $5M threshold proportion). Approximation.
            excess = deferred_principal - _453A_THRESHOLD
            a_453_interest_proxy = (
                deferred_tax * (excess / deferred_principal)
                * Decimal("0.045")  # proxy for AFR
            ).quantize(Decimal("0.01"))

        net_benefit = (npv_benefit - a_453_interest_proxy).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=max(net_benefit, Decimal(0)),
            savings_by_tax_type=TaxImpact(capital_gains_tax=max(net_benefit, Decimal(0))),
            inputs_required=[
                "installment note principal and schedule",
                "§453(i) ordinary recapture component (recognized year 1)",
                "§453A deferred-receivable balance for $5M threshold",
                "related-party buyer posture for §453(e) second-disposition rule",
                "pledge facts (§453A(d)) — pledged receivable deemed received",
            ],
            assumptions=[
                f"Target entity: {target_code}",
                f"Expected proceeds: ${proceeds:,.0f}",
                f"Seller basis: ${seller_basis:,.2f}",
                f"Gross gain: ${gross_gain:,.2f}",
                f"Deferred component pct: {deferred_pct:.0%}",
                f"Deferred principal: ${deferred_principal:,.2f}",
                f"Deferred gain: ${deferred_gain:,.2f}",
                f"Deferred tax at 23.8%: ${deferred_tax:,.2f}",
                f"Assumed installment length: {n} years at {_DISCOUNT_RATE:.0%} discount rate",
                f"PV of ratable tax stream: ${pv_of_ratable_tax:,.2f}",
                f"NPV benefit of deferral: ${npv_benefit:,.2f}",
                f"§453A interest exposure (> $5M): {a_453_exposure}",
                f"§453A interest proxy: ${a_453_interest_proxy:,.2f}",
            ],
            implementation_steps=[
                "Structure deal with installment note or earnout instead of "
                "all-cash close. Document seller note terms (AFR, security, "
                "maturity).",
                "File Form 6252 each year a payment is received.",
                "Recognize §453(i) ordinary recapture (§1245 / §1250) in full "
                "in year of sale — installment deferral applies only to "
                "capital gain balance.",
                "If deferred principal > $5M, track §453A(c) interest annually "
                "(Form 1040 line 17 via Schedule 2).",
                "Avoid related-party buyer §453(e) second-disposition trap: "
                "if buyer resells within 2 years, gain accelerates to seller.",
                "Do NOT pledge the installment note as collateral for seller's "
                "borrowing (§453A(d)) — triggers deemed receipt.",
            ],
            risks_and_caveats=[
                "§453 does not apply to publicly-traded stock, dealer "
                "dispositions, inventory, or sales of depreciable property "
                "between related parties without anti-abuse safe harbors.",
                "CA sources the gain to CA based on residency at PAYMENT "
                "receipt, not at sale — installment over a domicile break "
                "can avoid CA tax on out-of-state residency years.",
                "Contingent earnouts (§453 open-transaction / §15A.453-1(c)): "
                "applicable but basis recovery is ratable not proportionate. "
                "Consider INST_CONTINGENT_PAYMENTS for earnout-heavy deals.",
                "§453A interest expense is NOT deductible for individuals; "
                "for partnerships / S corps it flows through on K-1.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "SALE_INSTALLMENT",
                "SALE_EARNOUTS",
                "SALE_ASSET_VS_STOCK",
                "INST_ELECTION_OUT",
                "INST_CONTINGENT_PAYMENTS",
                "INST_RECAPTURE_ACCEL",
                "CA_INSTALLMENT_SOURCING",
                "NIIT_INSTALL_TIMING",
            ],
            verification_confidence="high",
            computation_trace={
                "target_entity_code": target_code,
                "expected_proceeds": str(proceeds),
                "seller_basis": str(seller_basis),
                "gross_gain": str(gross_gain),
                "deferred_component_pct": str(deferred_pct),
                "deferred_principal": str(deferred_principal),
                "deferred_gain": str(deferred_gain),
                "deferred_tax_at_23_8_pct": str(deferred_tax),
                "pv_of_ratable_tax": str(pv_of_ratable_tax),
                "npv_benefit": str(npv_benefit),
                "exceeds_453a_5m_threshold": a_453_exposure,
                "a_453_interest_proxy": str(a_453_interest_proxy),
                "net_benefit": str(net_benefit),
            },
        )
