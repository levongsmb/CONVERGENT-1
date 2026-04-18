# 0002 — Rules cache bootstrap sources and cadence

- **Status:** OPEN
- **Opened:** 2026-04-18
- **Phase gate:** Phase 0

## Context

§12A.5 and §12A.14 enumerate the primary-authority sources polled by the
Statutory Mining subsystem. The Phase 0 bootstrap must use the subset of
those sources that can be polled once and turned into a first-pass cache.

§4 is explicit: **secondary sources never set numbers**. The bootstrap may
use secondary sources (CPE volumes, publisher guides) for *coverage maps* —
"which statutory parameters does our engine need?" — but the values
themselves must come from primary authority.

## Options considered

### Option A — Full poll on bootstrap run

Statutory Mining polls every source in §12A.14 at install time. Cache is
fully current on Day 1.

- Pros: comprehensive; freshest possible Day-1 state
- Cons: long bootstrap (10+ minutes); dependent on every source being
  available; fragile; some sources (eCFR diff, court opinions) are huge

### Option B — Static seed shipped with installer, Statutory Mining refreshes on-demand thereafter

Bootstrap ships pre-computed from a build-time run. First launch does not
poll; user can trigger refresh from the UI.

- Pros: fast first-launch; predictable; reproducible across machines
- Cons: bootstrap is only as current as the build date; freshness banner
  will read red immediately on installers > 30 days old

### Option C — Hybrid: static seed + background refresh on first launch + Settings toggle

Ship a static seed. On first launch, kick off a background Statutory Mining
refresh that catches up to current. User can use the app immediately with
the seed; the app surfaces "refreshing authority cache" as an info banner
until the catch-up completes.

- Pros: fast launch, current cache within minutes, no user surprise
- Cons: slight behavioral complexity; must design the UI so stale cache
  doesn't silently taint early use

## Recommendation

**Option C.** Matches the prompt's freshness-banner discipline (§12A.9) and
avoids the static-shipped-cache trap where a 3-month-old installer produces
3-month-old commentary.

## Answer

(awaiting user)

## Implementation notes

(to be filled in)
