# 0003 — OBBBA bootstrap snapshot date

- **Status:** ANSWERED
- **Opened:** 2026-04-18
- **Answered:** 2026-04-18
- **Phase gate:** Phase 0

## Context

§12A.14 requires: "install-time cache includes the exact Public Law 119-21
text, the IRS 'One Big Beautiful Bill provisions' landing page content as
of release, and each Notice in the OBBBA interpretive series published prior
to build date."

The rules cache bootstrap needs a pinned snapshot date that defines:

- Which OBBBA interpretive Notices are in-cache on Day 1
- Which indexed amounts (retirement limits, AMT exemptions, estate
  exemptions) reflect OBBBA overrides vs. pre-OBBBA conformity
- Which sunset entries in the Sunset Watch pitfall list are active

Today's date is 2026-04-18. OBBBA (Public Law 119-21) was enacted in 2025.
The IRS has been releasing interpretive Notices on a rolling basis.

## Options considered

### Option A — Snapshot = build date

Bootstrap captures OBBBA authority as of the build date. Every installer
ships with a snapshot equal to its build day.

- Pros: freshest at install; matches user expectation
- Cons: installer-to-installer drift; reproducibility across installs varies

### Option B — Snapshot = latest IRS OBBBA interpretive Notice as of build date, date explicitly surfaced

Bootstrap captures OBBBA authority up to and including the most recent
Notice published as of the build run. The snapshot date is pinned in the
rules cache and surfaced in the app top-bar freshness indicator.

- Pros: explicit and auditable; reproducible given the same build date
- Cons: requires the Statutory Mining bootstrap to enumerate exactly which
  Notices are included

### Option C — Snapshot explicitly set by user at install

Installer prompts for target snapshot date; Statutory Mining rolls cache to
that date.

- Pros: maximum user control
- Cons: unnecessary friction; no normal user workflow justifies this

## Recommendation

**Option B.** The snapshot date and the enumerated Notices ship in
`rules_cache_bootstrap/manifest.yaml` and are visible in the UI. Any
engagement pins to a specific snapshot ID (§7 `rules_cache_snapshot_id`), so
memo reproducibility is preserved regardless of how far the live cache has
advanced.

## Answer

**2026-04-18:** Option B — snapshot date = build date (2026-04-18 for
this run); enumerated Notices and snapshot ID pinned in every engagement.
Notice scope answered separately in Decision 0008: narrow to the 13
return-line-impact OBBBA provisions.
