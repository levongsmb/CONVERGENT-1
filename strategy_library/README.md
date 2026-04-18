# Strategy Library

Per §12 of the build prompt, this directory is the deterministic catalog
of tax planning strategies Convergent selects from. It is the **ground
truth** for Strategy matching (§13) and scenario bundle composition
(§14).

## Structure

- `MANIFEST.yaml` — the complete enumeration of strategy IDs by category.
  Phase 0 deliverable. User reviews for category ordering (Open Question
  Q0.6) before Phase 1 begins.
- `{category}/{strategy_id}.yaml` — one file per strategy. Landed in
  Phase 1 sub-phases, one category at a time, with each category
  reviewed before the next begins.
- `pitfalls.yaml` — moved to `authority_layer/pitfalls.yaml` (§12A.10).

## Schema

Every strategy conforms to the §12.1 schema:

```yaml
id: string
name: string
category: enum
code_sections: [string]
applicable_entity_types: [EntityType]
triggering_facts: [Predicate]       # §12.3 DSL
preconditions: [Predicate]
contraindications: [Predicate]
mechanism: string                    # 1-paragraph plain-English
quantification: QuantificationSpec   # references Python quantify fn
audit_risk_score: 1..5
aggression_required: 1..5
complexity_level: 1..5
horizon_required: 1..5
obbba_effect: enum                   # UNCHANGED | PARAMETER_UPDATED | NEWLY_AVAILABLE | SUNSET_INTRODUCED | REPEALED
obbba_note: string
implementation_steps: [ImplementationStep]
planning_tips: [string]
dependencies: [string]
conflicts: [string]
primary_authority: [Citation]
secondary_reference: [string]
cost_of_advice_profile: CostProfileRef
memo_template: string                # Jinja2 template string or file path
client_facing_description: string
```

## Separation of concerns

The Strategy Library is **conceptual and durable** — strategy IDs,
trigger predicates, Code-section anchors, mechanism text. It does **not**
carry dollar amounts, percentages, sunset dates, or indexed thresholds.
Those come exclusively from the rules cache (populated by Statutory
Mining per §12A.14) at runtime.

The Citation Verifier (§12A.8) enforces this by rejecting any numerical
claim in generated output that cannot be pin-cited to primary authority
currently in the authority cache.

## Phase status

- **Phase 0:** `MANIFEST.yaml` published with 187 strategy IDs across 20
  categories (well above the §12.5 minimum of 120). Strategy YAML files
  are not yet written.
- **Phase 1:** strategies written one category at a time per the Q0.6
  ordering, with user review per category before advancing.

See `docs/decisions.md` for the per-category sign-off trail.
