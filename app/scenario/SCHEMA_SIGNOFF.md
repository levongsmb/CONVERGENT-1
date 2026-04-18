# G1 — Phase 1a Scenario Schema Sign-Off

Firm: SMB CPA Group, PC
Reviewer of record: Levon Galstian, CPA (License 146973)
Build spec section: 2 (Client Scenario Schema) and Section 8 (Sign-Off Gates)

This gate certifies that the Client Scenario Schema (Layer 2) is ready to
consume and that Phase 1b (Strategy Library Inventory) may begin.

## Deliverables produced under G1

| # | Deliverable | Path |
|---|-------------|------|
| 1 | Pydantic v2 models covering every spec §2.2 model | `app/scenario/models.py` |
| 2 | Full 50-state + DC + US-territory `StateCode` enum | `app/scenario/models.py` |
| 3 | Cross-field validators beyond model-level invariants | `app/scenario/validators.py` |
| 4 | Auto-generated JSON-Schema-as-YAML export for review | `app/scenario/schema.yaml` |
| 5 | Fixture loader consumed by tests and future orchestrator | `app/scenario/loader.py` |
| 6 | Seven realistic planning scenarios per spec §2.3 | `app/scenario/fixtures/*.yaml` |
| 7 | Pytest suite covering parse, validator invariants, Decimal precision, model-level refusals | `app/tests/scenarios/test_fixtures_parse.py` |

## Fixture inventory (spec §2.3)

| File | Pattern | Notes |
|------|---------|-------|
| `scenario_single_1040.yaml` | Single W-2 earner, no businesses, no dependents, 1040-only | Baseline for evaluators that must short-circuit. |
| `scenario_mfj_scorp_owner.yaml` | MFJ, primary owns 100% S corp with QBI; two minor dependents | QBI / reasonable-comp / PTET analysis triggers. Primary SMB CPA Group archetype. |
| `scenario_partnership_owner.yaml` | MFJ, 35% active LLC-as-partnership member | §1402(a)(13) Soroban posture, §704(d) basis, guaranteed payments vs distributive share, CA PTET credit attribution. |
| `scenario_real_estate_investor.yaml` | MFJ, three rentals, commercial cost-seg candidate, REP question | §469 passive, §469(c)(7) REP election, §168(k) bonus + CA §168(k) nonconformity, cost segregation. |
| `scenario_qsbs_founder.yaml` | Single founder, pre-IPO C corp, pre- and post-OBBBA §1202 lots | Holding-period tiering, pre/post-OBBBA regime tracking, CA §1202 nonconformity, gift-and-stack analysis, planned liquidity event. |
| `scenario_trust_beneficiary.yaml` | MFJ, beneficiary of nongrantor trust with K-1 distributions | DNI mechanics, §663(b) 65-day election interaction, §1411 posture. |
| `scenario_liquidity_event.yaml` | MFJ, 100% S corp owner, planned sale 18 months out, ~$18M EV | Asset vs stock, F-reorg, §338(h)(10), pre-sale basis cleanup, charitable bunching, CA PTET modeling, installment-note structuring. |

## Decimal precision and type strictness

- All dollar amounts use `decimal.Decimal`. Tests assert round-trip
  preservation through YAML (spec Section 2.4, checkbox 5).
- All dates use `datetime.date`.
- `Optional[...]` defaults to `None`; no implicit zeros for fields that
  should be missing.
- Enums (`FilingStatus`, `EntityType`, `StateCode`, `AssetType`) use
  strict string enums so typos in YAML fail at parse time.
- Ownership percentage fields enforce `ge=0, le=100` at the Pydantic layer.
- `tax_year` enforces `ge=2020, le=2040`; `time_horizon_years` enforces
  `ge=0, le=50`.

## Validator coverage

Model-level validators (in `models.py`, always executed by Pydantic):

- `validate_k1_consistency` — rejects any K-1 whose `entity_code` does
  not appear in the scenario's `entities` list. Confirmed by
  `test_k1_orphan_raises`.
- `validate_filing_status_spouse_consistency` — rejects MFJ/MFS without
  `spouse_dob`, and SINGLE with `spouse_dob`. Confirmed by two tests.

Cross-field diagnostic checks (in `validators.py`, explicit call):

- Entity ownership percentages within [0, 100]
- QSBS assets must carry issuance date, pre/post-OBBBA flag, and issuer EIN
- S corp entities must carry `stock_basis` (otherwise §1366(d) cannot run)
- Partnership entities must carry `outside_basis` (otherwise §704(d) cannot run)
- `liquidity_event_planned` shape check (requires `target_close_date` and
  `expected_proceeds`); presence required when
  `LIQUIDITY_EVENT_PREP` is in objectives
- State-sourcing multi-state items must include the resident state
- Dependents must carry `relationship` and `dob`
- Informational flag when both spouses domicile in community property
  states and filing MFS

## State nonconformity support (spec §2.4, checkbox 3)

- `Entity.operating_states: List[StateCode]` supports multi-state apportionment.
- `Asset.state_nonconformity_basis: Dict[StateCode, Decimal]` tracks basis
  divergences for CA §168(k) (bonus nonconformity), CA §1202 (QSBS
  exclusion nonconformity), and any other state that does not conform to
  federal basis. Exercised in the real-estate and QSBS fixtures.
- `Asset.qsbs_pre_or_post_obbba: Literal["PRE", "POST"]` branches
  computations between pre- and post-OBBBA §1202 rule sets.
- `K1Income.state_pte_credit_attributable: Dict[StateCode, Decimal]`
  carries state-by-state PTET credit allocations from upstream entities.
- `Identity.primary_state_domicile` and `spouse_state_domicile` plus
  community-property detection in validators support CA community
  property splits.

## Test result

```
$ pytest app/tests/scenarios/
22 passed in 0.51s
```

Coverage: all seven fixtures parse; all seven pass the cross-field
validator with zero blocking diagnostics; model-level refusals confirmed
against three negative cases (orphan K-1, MFJ without spouse_dob, SINGLE
with spouse_dob); Decimal precision preserved end-to-end through YAML.

## Sign-off (spec §2.4 checklist)

- [x] Pydantic models cover all fact patterns in SMB CPA Group client base
- [x] Validators catch cross-field inconsistency (K-1 references,
      filing status / spouse)
- [x] State sourcing fields support CA nonconformity for QSBS, bonus
      depreciation, community property
- [x] Fixtures represent realistic scenarios for seven planning patterns
- [x] Decimal precision and type strictness appropriate for tax computation

Signed: Levon Galstian, CPA
Date: 2026-04-18
