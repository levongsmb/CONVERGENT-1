# 0007 — Review method = per-file SIGNOFF.md companions

- **Status:** ANSWERED
- **Opened:** 2026-04-18
- **Answered:** 2026-04-18
- **Phase gate:** Phase 0 acceptance

## Context

Q0.1 offered three review methods. User picked (b) per-file SIGNOFF.md
companions for parameter-level accountability and asynchronous
review.

## Answer

**2026-04-18:** Every YAML in `rules_cache_bootstrap/` that is reviewed
gets a companion file with the same stem plus `.SIGNOFF.md`. Master
checklist (`review_checklist.md`) is retained as a navigation index only
and is updated automatically from the SIGNOFF file set — it does not
duplicate sign-off records.

## Implementation notes

- Template lives at `rules_cache_bootstrap/_SIGNOFF_TEMPLATE.md`.
- Each SIGNOFF file carries (per parameter): `signed_off` /
  `corrected` / `needs_review`, the reviewer's initials, date, and
  a correction note when applicable.
- Phase 0 acceptance is met when every YAML in `rules_cache_bootstrap/`
  has a matching SIGNOFF file with every parameter either `signed_off`
  or `corrected`, and the master line `Signed off: <date> — <initials>`
  in `review_checklist.md` is present.
- Claude Code does not write the SIGNOFF files for parameters it cannot
  authoritatively confirm; the CPA is the reviewer of record.