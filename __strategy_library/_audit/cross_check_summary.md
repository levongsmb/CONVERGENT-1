# G4 — Phase 2 Cross-Check Protocol Summary

Firm: SMB CPA Group, PC
Reviewer of record: Levon Galstian, CPA (License 146973)
Build spec section: 4 (Phase 2 Cross-Check Protocol) and Section 8 (Sign-Off Gates)

This gate certifies that the Phase 2 cross-check infrastructure is in
place, tested, and that the planned work is understood before any real
LLM API calls are made.

## Deliverables produced under G4

| # | Deliverable | Path |
|---|-------------|------|
| 1 | Cross-check runner package | `app/cross_check/` (`runner.py`, `null_detection.py`, `merge.py`, `audit.py`, `__main__.py`) |
| 2 | Test suite (16 tests) | `app/tests/cross_check/test_cross_check.py` |
| 3 | Dry-run audit log | `__strategy_library/_audit/cross_check_2026-04-18.jsonl` (616 rows) |
| 4 | Config validator pass | `python -m app.config.validate` returns `passed` |
| 5 | Full test suite pass | `pytest app/tests/` returns 48 passed |

## Dry-run statistics (2026-04-18)

Executed `python -m app.cross_check --quiet --today-date 2026-04-18` with
the default `--dry-run` flag. Source: `__strategy_library/subcategories/`
containing 40 category YAMLs and 616 subcategories.

| Metric | Value |
|---|---|
| Total subcategories in library | 616 |
| Subcategories needing cross-check | 616 |
| Subcategories already marked manual or retry | 0 |
| Unique prompt hashes produced | 616 (no collisions) |
| Missing-field pattern count | 6 distinct patterns |

### Missing-field pattern distribution

| Count | Missing fields (all 6 of the §4 trigger set) |
|------:|-----|
| 467 | entity_applicability, jurisdiction_tags, obbba_touched, priority_score, statutory_cite, tax_type_impacted |
| 114 | entity_applicability, jurisdiction_tags, obbba_touched, statutory_cite, tax_type_impacted (priority_score already inline) |
| 16 | entity_applicability, jurisdiction_tags, priority_score, tax_type_impacted (statutory_cite and obbba_touched already inline) |
| 10 | entity_applicability, jurisdiction_tags, priority_score, statutory_cite, tax_type_impacted (obbba_touched already inline) |
| 6 | entity_applicability, jurisdiction_tags, tax_type_impacted (priority_score, obbba_touched, statutory_cite all inline) |
| 3 | entity_applicability, jurisdiction_tags, statutory_cite, tax_type_impacted |

Every subcategory is missing at least `entity_applicability`,
`jurisdiction_tags`, and `tax_type_impacted` — those three fields were
never populated inline in spec §3.3 and are expected to come exclusively
from the Phase 2 protocol. The 149 subcategories carrying inline cites,
priority scores, or obbba_touched flags at G3 will have those values
preserved by the merge layer; the cross-check populates only the fields
that are null or blank.

## Cost estimate for the real run

Inputs per call (after Jinja render of the `cross_check_subcategory.j2`
template, the parent_category token, and the subcategory fields): on the
order of 700 input tokens and ~350 output tokens (constrained JSON
schema). Prices pinned in `config/models.yaml` point the `bulk_cross_check`
task class at `claude-sonnet-4-6` and the escalation route at
`claude-opus-4-7`.

| Scenario | Estimated cost |
|---|---|
| Single pass through all 616 subcategories, no escalations | ~$4.50 |
| Worst case with 100% escalation to Opus 4.7 | up to ~$27 |
| Expected case (low-confidence escalation rate ~10-15%) | ~$7-10 |

Cost is small relative to the audit value; the protocol is safe to run
in full.

## Architecture summary

```
               ┌────────────────────────────┐
               │  python -m app.cross_check │
               └──────────┬─────────────────┘
                          │
                          ▼
             ┌───────────────────────────┐
             │  runner.run_all()         │
             │   - iterate MANIFEST      │
             │   - for each subcategory: │
             │       needs_cross_check() │
             │       render prompt       │
             │       LLMClient.call()    │
             │       parse JSON          │
             │       escalate if low     │
             │       merge to YAML       │
             │       audit.append()      │
             │   - checkpoint every 50   │
             └────────┬──────────────────┘
                      │
          ┌───────────┼───────────────────────┐
          ▼           ▼                       ▼
  ┌────────────┐ ┌──────────┐  ┌──────────────────────────┐
  │ app.config │ │ anthropic│  │ __strategy_library/      │
  │ .router    │ │ SDK      │  │   subcategories/*.yaml   │
  │ .prompts   │ │          │  │ __strategy_library/      │
  └────────────┘ └──────────┘  │   _audit/cross_check_*   │
                               └──────────────────────────┘
```

All model strings resolve through `config/models.yaml`. All prompt
wording lives in `config/prompts/cross_check_subcategory.j2`. No Python
code contains a model string or a prompt fragment.

## Failure-handling behavior (spec §4.3, verified by tests)

- **JSON parse failure.** First response fails to parse as JSON → the
  runner retries once with identical parameters. A second failure marks
  the subcategory `cross_check_required: "manual"` and advances.
  (Verified by `test_run_all_json_parse_failure_retries_then_marks_manual`.)
- **API error.** Any exception from the Anthropic SDK (rate limit,
  timeout, HTTP error) marks the subcategory `cross_check_required: "retry"`
  and advances. The next run with `--include-manual-retry` picks these up.
  (Verified by `test_run_all_api_error_marks_retry`.)
- **Low-confidence escalation.** A successfully-parsed response whose
  `verification_confidence == "low"` triggers a second call against the
  `complex_reasoning` task class (opus-4-7). The escalated response
  replaces the sonnet response. (Verified by
  `test_run_all_escalates_on_low_confidence`.)
- **Checkpointing.** Every 50 processed subcategories (or at run end),
  dirty category YAML files are written back. Partial-run crashes lose
  at most 50 subcategories of work.
- **Merge preserves inline values.** Existing non-null fields are never
  overwritten. The LLM may return a different `statutory_cite` than the
  hand-curated one in spec §3.3; the curated cite wins. (Verified by
  `test_apply_cross_check_response_populates_nulls_only`.)

## How to invoke the real run (user-executed)

```bash
# 1. Confirm ANTHROPIC_API_KEY is available (env var, or keyring on Windows)
echo $ANTHROPIC_API_KEY | head -c 10

# 2. (Optional) Re-run dry-run to confirm current null posture
python -m app.cross_check --today-date 2026-04-18

# 3. Real run
python -m app.cross_check --real --today-date 2026-04-18

# 4. Follow-up pass for anything flagged "retry" or "manual"
python -m app.cross_check --real --include-manual-retry --today-date 2026-04-18
```

Expected walltime on the default `batch_size: 20` / `batch_delay_seconds: 1`
settings in `config/models.yaml`: approximately 20-40 minutes for 616
subcategories depending on Anthropic-side latency.

## G4 Sign-off

- [ ] Cross-check runner architecture matches spec §4 (task-class routing,
      escalation path, JSON-only output, batch defaults honored)
- [ ] Failure handling matches spec §4.3 (JSON retry → manual;
      API error → retry; checkpoint every 50)
- [ ] Dry-run confirms 616 subcategories need cross-check across 40
      categories with 616 unique prompt hashes (no collisions)
- [ ] Cost envelope acceptable (expected ~$7-10, worst case ~$27)
- [ ] Test suite green (`pytest app/tests/cross_check/` → 16 passed)
- [ ] Approval to proceed with real run on the firm's Anthropic API key

Signed: __________________________________
Date: __________________________________
