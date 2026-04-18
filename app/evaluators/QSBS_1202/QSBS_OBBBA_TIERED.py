"""QSBS_OBBBA_TIERED — 50/75/100% tiered exclusion computation (post-OBBBA).

For QSBS issued after 2025-07-04 under OBBBA §70431, applies the
holding-period-based exclusion tier to each lot and quantifies the
excluded and taxable portions. Pre-OBBBA lots use the strict 5-year
100% rule (QSBS_HOLDING_PERIOD surfaces the regime). This evaluator
computes dollar exclusion at the current or next-tier state.
"""

from __future__ import annotations

from decimal import Decimal
from datetime import date, timedelta
from typing import Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario


_OBBBA_EFFECTIVE_DATE = date(2025, 7, 4)


def _param(doc: dict, regime: str, sub: str) -> Optional[Decimal]:
    for p in doc.get("parameters", []):
        c = p.get("coordinate", {})
        if c.get("regime") == regime and c.get("sub_parameter") == sub:
            v = p.get("value")
            if v is None:
                return None
            try:
                return Decimal(str(v))
            except Exception:
                return None
    return None


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "QSBS_OBBBA_TIERED"
    CATEGORY_CODE = "QSBS_1202"
    PIN_CITES = [
        "IRC §1202(a) as amended by OBBBA §70431 — 50/75/100% tiered exclusion",
        "IRC §1202(b)(1)(A) — per-issuer $15M dollar cap (OBBBA)",
        "IRC §1202(b)(1)(B) — 10× basis alternative cap",
        "IRC §1(h)(4) — 28% rate on non-excluded §1202 gain",
        "IRC §1411 — NIIT exclusion on §1202-excluded gain (§1.1411-10)",
        "P.L. 119-21 §70431 — OBBBA §1202 amendments",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        qsbs_lots = [
            a for a in scenario.assets
            if a.is_qsbs
            and a.qsbs_issuance_date is not None
            and a.fmv is not None
            and a.adjusted_basis is not None
        ]
        if not qsbs_lots:
            return self._not_applicable(
                "no QSBS-flagged assets with issuance_date + FMV + basis; "
                "OBBBA-tiered exclusion math requires complete metadata"
            )

        doc = rules.get("federal/section_1202", year)
        per_issuer_cap = _param(doc, "OBBBA", "per_issuer_cap_dollar_component") or Decimal("15000000")
        basis_multiplier = _param(doc, "OBBBA", "per_issuer_cap_basis_multiplier") or Decimal("10")

        ref_date = date(year, 12, 31)
        lot_details: list = []
        total_excluded = Decimal(0)
        total_taxable = Decimal(0)
        for a in qsbs_lots:
            issuance = a.qsbs_issuance_date
            regime = (
                a.qsbs_pre_or_post_obbba
                or ("POST" if issuance > _OBBBA_EFFECTIVE_DATE else "PRE")
            )
            gain = a.fmv - a.adjusted_basis
            if gain <= Decimal(0):
                continue
            days_held = (ref_date - issuance).days
            years_held = Decimal(days_held) / Decimal("365.25")

            if regime == "PRE":
                exclusion_pct = Decimal("1.00") if years_held >= Decimal(5) else Decimal("0.00")
            else:
                if years_held >= Decimal(5):
                    exclusion_pct = Decimal("1.00")
                elif years_held >= Decimal(4):
                    exclusion_pct = Decimal("0.75")
                elif years_held >= Decimal(3):
                    exclusion_pct = Decimal("0.50")
                else:
                    exclusion_pct = Decimal("0.00")

            # Per-issuer cap: greater of $15M or 10 × aggregated basis.
            # First-order proxy: apply to this lot in isolation.
            lot_cap = max(per_issuer_cap, a.adjusted_basis * basis_multiplier)
            excluded = min(gain * exclusion_pct, lot_cap)
            taxable = gain - excluded

            total_excluded += excluded
            total_taxable += taxable
            lot_details.append({
                "asset_code": a.asset_code,
                "regime": regime,
                "years_held": f"{years_held:.2f}",
                "exclusion_pct": str(exclusion_pct),
                "gain": str(gain),
                "lot_cap": str(lot_cap),
                "excluded": str(excluded),
                "taxable_at_28_pct": str(taxable),
            })

        # Tax savings vs a non-QSBS LTCG (23.8% LTCG+NIIT):
        # - Excluded portion: saves 23.8% of excluded_gain
        # - Non-excluded portion: taxed at 28% vs 23.8%, so costs
        #   an incremental 4.2% on the taxable portion.
        saved_on_excluded = (total_excluded * Decimal("0.238")).quantize(Decimal("0.01"))
        extra_cost_on_taxable = (total_taxable * Decimal("0.042")).quantize(Decimal("0.01"))
        net_fed_save = (saved_on_excluded - extra_cost_on_taxable).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=max(net_fed_save, Decimal(0)),
            savings_by_tax_type=TaxImpact(
                capital_gains_tax=max(net_fed_save, Decimal(0)),
            ),
            inputs_required=[
                "issuance date and regime per QSBS lot",
                "adjusted basis and current FMV per lot",
                "aggregate per-issuer basis for the 10× basis cap alternative",
                "planned sale timing (coordinate with QSBS_HOLDING_PERIOD next-tier vest)",
            ],
            assumptions=[
                f"OBBBA per-issuer dollar cap: ${per_issuer_cap:,.0f}",
                f"Alternative basis multiplier: {basis_multiplier}×",
                f"Aggregate gain across QSBS lots: "
                f"${total_excluded + total_taxable:,.2f}",
                f"Aggregate excluded: ${total_excluded:,.2f}",
                f"Aggregate taxable at §1(h)(4) 28%: ${total_taxable:,.2f}",
                "Federal saving vs non-QSBS LTCG (23.8%): "
                f"${saved_on_excluded:,.2f} saved on excluded minus "
                f"${extra_cost_on_taxable:,.2f} extra on non-excluded.",
            ],
            implementation_steps=[
                "Coordinate sale timing with next_tier_vest_date (see "
                "QSBS_HOLDING_PERIOD) to maximize exclusion percentage.",
                "Document the per-issuer cap calculation at sale date; $15M "
                "OBBBA cap is per-issuer, not per-taxpayer or per-trust.",
                "For pre-OBBBA lots, strict 5-year rule applies; no partial "
                "exclusion. Consider §1045 rollover if under 5y at sale date.",
                "For state conformity (CA), see QSBS_STATE_CONFORMITY — the "
                "exclusion is federal-only.",
            ],
            risks_and_caveats=[
                "Per-issuer cap is shared across all shareholders of the same "
                "issuer if gift-and-stacked via non-grantor trusts (QSBS_STACKING). "
                "Cap can be multiplied by trust count only if trusts are "
                "distinct §643(f) taxpayers.",
                "Non-excluded §1202 gain is taxed at §1(h)(4) 28% (collectibles "
                "rate), not the 20% LTCG rate. The overall QSBS benefit is "
                "still net positive in most cases but the 28% stack on the "
                "non-excluded portion chips the advantage.",
                "CA does not conform — full CA tax on the gross gain at "
                "ordinary rates. See QSBS_STATE_CONFORMITY.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "QSBS_HOLDING_PERIOD",
                "QSBS_ORIGINAL_ISSUANCE",
                "QSBS_OBBBA_15M_CAP",
                "QSBS_STACKING",
                "QSBS_STATE_CONFORMITY",
                "QSBS_1045_ROLLOVER",
                "CA_NONCONFORMITY_QSBS",
            ],
            verification_confidence="high",
            computation_trace={
                "per_issuer_cap": str(per_issuer_cap),
                "basis_multiplier": str(basis_multiplier),
                "lot_count": len(lot_details),
                "lot_details": lot_details,
                "total_excluded": str(total_excluded),
                "total_taxable_at_28_pct": str(total_taxable),
                "saved_on_excluded": str(saved_on_excluded),
                "extra_cost_on_taxable": str(extra_cost_on_taxable),
                "net_fed_save_vs_ltcg": str(net_fed_save),
            },
        )
