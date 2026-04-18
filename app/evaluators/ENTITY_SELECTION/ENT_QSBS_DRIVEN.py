"""ENT_QSBS_DRIVEN — convert pass-through to C corp before growth to
qualify future stock as §1202 QSBS.

Applicable when the taxpayer owns a pass-through with growth potential
and a planning horizon ≥ 3 years (to reach OBBBA's 50% exclusion tier)
or ≥ 5 years (full 100% exclusion). Under OBBBA §70431, QSBS issued
after 2025-07-04 qualifies for tiered exclusion (50% at 3y / 75% at 4y /
100% at 5y), up to the greater of $15M per-issuer cap or 10× basis.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import ClientScenario, EntityType


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "ENT_QSBS_DRIVEN"
    CATEGORY_CODE = "ENTITY_SELECTION"
    PIN_CITES = [
        "IRC §1202(a) and (b)(4) as amended by OBBBA §70431 — tiered exclusion",
        "IRC §1202(d) as amended by OBBBA — $75M gross-assets test",
        "IRC §1202(c) — original issuance requirement",
        "IRC §351 — tax-free incorporation",
        "IRC §358 — basis in stock received in §351 exchange",
        "IRC §1(h)(4) — 28% rate on non-excluded §1202 gain",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        pass_throughs = [
            e for e in scenario.entities
            if e.type in (
                EntityType.S_CORP, EntityType.LLC_S_CORP,
                EntityType.PARTNERSHIP, EntityType.LLC_PARTNERSHIP,
                EntityType.SOLE_PROP, EntityType.LLC_DISREGARDED,
            )
        ]
        if not pass_throughs:
            return self._not_applicable(
                "no pass-through entity to convert; ENT_QSBS_DRIVEN requires "
                "a target pass-through entity"
            )

        # Planning horizon signal
        horizon = scenario.planning.time_horizon_years
        liquidity = scenario.planning.liquidity_event_planned
        if horizon < 3 and liquidity is None:
            return self._not_applicable(
                f"planning horizon {horizon}y under 3y and no liquidity event "
                "planned; §1202 holding-period tiers start at 3y"
            )

        # Gross receipts / size gate
        s = rules.get("federal/section_1202", year)
        post_obbba_cap_usd = None
        post_obbba_gross_assets = None
        for p in s.get("parameters", []):
            coord = p.get("coordinate", {})
            if coord.get("regime") != "OBBBA":
                continue
            sp = coord.get("sub_parameter")
            if sp == "per_issuer_cap_dollar_component":
                post_obbba_cap_usd = Decimal(str(p["value"]))
            elif sp == "gross_assets_ceiling_at_issuance":
                post_obbba_gross_assets = Decimal(str(p["value"]))

        flagged: list = []
        for e in pass_throughs:
            if e.gross_receipts_prior_year is not None:
                if (
                    post_obbba_gross_assets is not None
                    and e.gross_receipts_prior_year > post_obbba_gross_assets * Decimal("0.5")
                ):
                    # Gross receipts proxy as a quick sanity check; gross
                    # ASSETS is the actual §1202(d) test. Phase 3b schema
                    # adds dedicated gross-assets field.
                    flagged.append((e.code, "LARGE_ENOUGH_FOR_GROSS_ASSETS_TEST"))
                else:
                    flagged.append((e.code, "BELOW_GROSS_ASSETS_PROXY"))

        # Qualitative benefit sizing: §1202 exclusion is up to post-OBBBA
        # $15M cap. Federal rate differential = 23.8% (LTCG 20% + NIIT 3.8%)
        # versus 0% on excluded gain — so potential savings up to
        # $15M × 23.8% = $3.57M per taxpayer per issuer on full exclusion.
        # Gift-and-stack multiplies by non-grantor trust count.
        cap = post_obbba_cap_usd or Decimal("15000000")
        max_per_taxpayer_savings = (cap * Decimal("0.238")).quantize(Decimal("0.01"))

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "entity gross assets at issuance (not just receipts)",
                "projected pre-liquidity FMV per shareholder's basis",
                "active trade or business verification (non-SSTB for §1202)",
                "planned non-grantor trust count (for gift-and-stack leverage)",
                "state conformity posture (CA does NOT conform to §1202)",
            ],
            assumptions=[
                f"Planning horizon: {horizon} years",
                f"OBBBA per-issuer cap: ${cap:,.0f}",
                f"Post-OBBBA gross-assets ceiling: "
                f"${post_obbba_gross_assets:,.0f}" if post_obbba_gross_assets else "awaiting rules cache",
                f"Max per-taxpayer federal savings on full exclusion (cap × 23.8%): "
                f"${max_per_taxpayer_savings:,.0f}",
                "CA does not conform to §1202; state tax remains on full gain.",
            ],
            implementation_steps=[
                "Verify entity is (or will be) a C corp and engaged in a "
                "qualified trade or business per §1202(e).",
                "For a pass-through: execute a §351 tax-free incorporation "
                "to a new C corp; QSBS holding period begins at issuance.",
                "For an LLC taxed as partnership: consider §351 via partnership "
                "incorporation, preserving §1202(a)(2) basis from partnership "
                "interest.",
                "Confirm gross assets at and immediately after issuance do "
                "not exceed §1202(d) ceiling (OBBBA $75M).",
                "Plan gift-and-stack via non-grantor trusts to multiply the "
                "per-issuer cap across multiple taxpayers (coordinate with "
                "QSBS_STACKING and TRUSTS_INCOME_SHIFTING).",
                "Document QSBS posture: Form 2553 withdrawn (if S), §351 "
                "exchange documentation, stock ledger, corporate records.",
            ],
            risks_and_caveats=[
                "Conversion to C corp exposes earnings to 21% corporate tax "
                "and potentially double tax on distributions. Pre-liquidity "
                "posture typically offsets via growth + §1202 exclusion, but "
                "ongoing operations inside the C corp cost tax dollars.",
                "The 5-year holding period is required for 100% exclusion "
                "post-OBBBA. 3-year and 4-year tiers give 50% and 75% only.",
                "Active business requirement: at least 80% of assets used in "
                "an active trade or business in a qualified field. Investment- "
                "holding structures fail.",
                "CA taxes the full gain at ordinary rates (up to ~13.3%); the "
                "federal exclusion does NOT flow through to CA.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "QSBS_ORIGINAL_ISSUANCE",
                "QSBS_HOLDING_PERIOD",
                "QSBS_OBBBA_TIERED",
                "QSBS_STACKING",
                "QSBS_GIFT_AND_STACK",
                "QSBS_STATE_CONFORMITY",
                "CA_NONCONFORMITY_QSBS",
            ],
            verification_confidence="medium",
            computation_trace={
                "horizon_years": horizon,
                "liquidity_event_planned": liquidity is not None,
                "post_obbba_cap_usd": str(cap),
                "post_obbba_gross_assets_ceiling": str(post_obbba_gross_assets) if post_obbba_gross_assets else None,
                "max_per_taxpayer_savings_full_exclusion": str(max_per_taxpayer_savings),
                "entity_flags": [
                    {"entity_code": c, "flag": f} for c, f in flagged
                ],
            },
        )
