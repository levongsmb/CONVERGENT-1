"""RED_163J_REPTOB — electing real property trade or business under §163(j)(7)(B).

An electing real-property trade or business ("RPTOB") is exempt from
§163(j) business interest limitation, but must depreciate 27.5-year
residential, 39-year nonresidential, and QIP under ADS (30, 40, and 20
years respectively), and forfeit §168(k) bonus.

Applicable when an entity has real property AND substantial business
interest expense that would be limited absent the election. The
election is IRREVOCABLE.
"""

from __future__ import annotations

from decimal import Decimal

from app.evaluators._base import BaseEvaluator, StrategyResult, TaxImpact
from app.scenario.models import AssetType, ClientScenario, EntityType


_REAL_PROPERTY_TYPES = {
    AssetType.REAL_PROPERTY_COMMERCIAL,
    AssetType.REAL_PROPERTY_RESIDENTIAL,
    AssetType.REAL_PROPERTY_LAND,
    AssetType.REAL_PROPERTY_FARMLAND,
}


class Evaluator(BaseEvaluator):
    SUBCATEGORY_CODE = "RED_163J_REPTOB"
    CATEGORY_CODE = "REAL_ESTATE_DEPRECIATION"
    PIN_CITES = [
        "IRC §163(j)(7)(B) — electing real property trade or business",
        "IRC §168(g) — Alternative Depreciation System required post-election",
        "IRC §168(k)(9)(A) — bonus disallowed for ADS property",
        "Rev. Proc. 2019-8 — election procedure",
        "Rev. Proc. 2020-22 — late or withdrawn election",
    ]

    def evaluate(self, scenario: ClientScenario, rules, year: int) -> StrategyResult:
        has_real_property = any(
            a.asset_type in _REAL_PROPERTY_TYPES for a in scenario.assets
        )
        rental_entity = any(
            e.type in (EntityType.LLC_DISREGARDED, EntityType.LLC_PARTNERSHIP,
                       EntityType.PARTNERSHIP, EntityType.S_CORP, EntityType.LLC_S_CORP)
            for e in scenario.entities
        )

        if not has_real_property and not rental_entity:
            return self._not_applicable(
                "no real property or rental entity in scenario; §163(j)(7)(B) "
                "election is real-property-specific"
            )

        prior_163j = scenario.prior_year.suspended_163j_carryover

        return StrategyResult(
            subcategory_code=self.SUBCATEGORY_CODE,
            applicable=True,
            estimated_tax_savings=Decimal(0),
            savings_by_tax_type=TaxImpact(),
            inputs_required=[
                "entity business interest expense",
                "entity ATI under OBBBA EBITDA method",
                "real property basis and remaining MACRS life",
                "pending §168(k) bonus plans for property not yet in service",
                "election posture (once made, irrevocable)",
            ],
            assumptions=[
                "§163(j)(7)(B) election is IRREVOCABLE once filed.",
                "Post-election, ADS applies: 30 years residential, 40 years "
                "nonresidential, 20 years QIP. Bonus §168(k) disallowed.",
                f"Prior §163(j) carryover balance: ${prior_163j:,.2f}",
            ],
            implementation_steps=[
                "Quantify the annual §163(j) disallowance absent the election "
                "(LL_163J_INTEREST provides the base).",
                "Quantify the lost bonus depreciation and longer ADS recovery "
                "if the election is made (compare present value of deductions).",
                "File the §1.163(j)-9(e) election with the original return on "
                "the first year the election is effective (no late-filing "
                "relief except via Rev. Proc. 2020-22).",
                "Apply ADS to existing and subsequently-acquired real property "
                "of the electing trade or business.",
                "Pair with RED_COST_SEG outcome: post-election, cost-seg "
                "components move to ADS lives (shorter periods than the "
                "building but ADS-constrained).",
            ],
            risks_and_caveats=[
                "Once elected, the electing trade or business CANNOT revoke "
                "without Commissioner consent. The election binds all current "
                "and future real property of the electing activity.",
                "Aggregated §163(j) analysis: if the entity has both real- "
                "property and non-real-property activities, the election "
                "applies only to the real-property trade or business — but "
                "allocation of interest, ATI, and basis requires reasonable "
                "methods under §1.163(j)-10.",
                "Bonus forfeited is retroactive to the election year for "
                "unplaced property, and prospective only for already-placed "
                "property.",
            ],
            pin_cites=list(self.PIN_CITES),
            cross_strategy_impacts=[
                "LL_163J_INTEREST",
                "LL_163J_EBITDA_OBBBA",
                "RED_COST_SEG",
                "RED_BONUS_DEPR",
                "RED_ADS_VS_GDS",
                "AM_481A_PLANNING",
            ],
            verification_confidence="high",
            computation_trace={
                "has_real_property": has_real_property,
                "has_rental_entity": rental_entity,
                "prior_163j_carryover": str(prior_163j),
                "election_irrevocable": True,
            },
        )
