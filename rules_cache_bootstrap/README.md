# Rules Cache Bootstrap — Phase 0 Deliverable

This directory is the **Phase 0 gate artifact**. Per §18 of the build prompt,
Phase 1 cannot begin until the user personally signs off every rule
parameter here.

## What's in this directory

One YAML file per rule-parameter family. Each file groups parameters by
the Code / RTC section they implement. Every parameter carries:

- `tax_year` — the year the value applies to
- `value` — dollar amount, percentage, ratio, or enum
- `unit` — USD | PCT | RATIO | COUNT | DATE | ENUM
- `authority_kind` — IRC | REG | REV_PROC | REV_RUL | NOTICE | PL | RTC | FTB_NOTICE
- `authority_citation` — specific cite (e.g., "Rev. Proc. 2025-32 §3.06")
- `authority_url` — resolvable public URL to primary authority
- `retrieved_at` — when Claude Code populated the value
- `verification_status` — `bootstrapped` | `verified_by_cpa` | `awaiting_user_input` | `needs_review`
- `notes` — optional context

## Decision 0001 (Option C) — what Claude Code populated vs. what it did not

Claude Code pre-populated every parameter for which a current pin cite to
primary authority was reliably available at build time. Parameters that
depend on:

- Rev. Procs not yet released for the planning year
- OBBBA interpretive Notices with open implementation questions
- User-judgment decisions still open in `docs/decisions/`

are marked `verification_status: awaiting_user_input` with the specific
authority the value will come from once available. **These are the
blocking items for Phase 0 sign-off.**

## Review workflow

Per open-question Q0.1 in `OPEN_QUESTIONS.md`, the user must pick a review
mode. Default proposal (Option B from Q0.1): for each YAML here, the user
creates a companion `<filename>.SIGNOFF.md` in the same directory that:

1. Lists every parameter with its value
2. Records the user's sign-off (initials + date) per parameter, or a
   correction
3. Records any parameter moved to the `needs_review` bucket for re-sourcing

When every YAML in this directory has a matching `.SIGNOFF.md` with every
parameter either `signed_off` or `corrected`, Phase 0 acceptance is
achieved. Claude Code reads the SIGNOFF files and either advances to Phase 1
or cycles back to correct flagged parameters.

## Files

- `federal/` — Federal rule parameters, grouped by Code section
- `california/` — CA rule parameters
- `multistate/` — multi-state frameworks (apportionment, throwback, etc.)
- `obbba_notices.yaml` — enumerated OBBBA interpretive Notices in the
  bootstrapped snapshot (per Decision 0003)
- `listed_transactions.yaml` — current IRS Listed Transaction designations
- `reportable_transactions.yaml` — current Reportable Transaction
  designations
- `review_checklist.md` — the master cross-reference of every parameter
  and its sign-off state

## Scope and pragmatic caveats

The Phase 0 bootstrap targets the **minimum parameter set the engine needs
for the golden-scenario suite**. That includes: federal brackets,
standard deduction, AMT exemption, NIIT thresholds, Additional Medicare
threshold, Social Security wage base, Medicare wage base,
retirement-plan §402(g) / §414(v) / §415(c) / §401(a)(17) limits, estate
and gift exemption + annual exclusion, SALT cap, §199A thresholds,
§461(l) limits, §163(j) small-corp thresholds, §448(c) small-corp
threshold, §1202 gain-exclusion cap, §1411 brackets, CA §17041 brackets,
CA AMT, CA Mental Health Services Tax, CA PTET parameters (see
Decision 0004), CA SDI wage base, and PTET-era multistate analogs.

Values that depend on proprietary or paywalled sources (any CCH / RIA /
BNA content) are **never** placed here. If a value requires a
non-primary source, it is `awaiting_user_input` with a note directing
the user to supply the current value or their preferred authority cite.
