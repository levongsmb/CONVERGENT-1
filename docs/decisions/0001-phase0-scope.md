# 0001 — Phase 0 scope

- **Status:** OPEN
- **Opened:** 2026-04-18
- **Answered:** —
- **Implemented:** —
- **Phase gate:** Phase 0 acceptance

## Context

§18 of the build prompt specifies Phase 0 deliverables:

1. Repo structure, `pyproject.toml`, pinned dependencies
2. SQLite schemas for engagement, rules cache, authority cache
3. Statutory Mining subsystem scaffolding **plus a bootstrap run populating
   every rule parameter the v1 engine needs at current post-OBBBA values**
4. `decisions.md`, `OPEN_QUESTIONS.md`, `CHANGELOG.md`
5. Windows installer skeleton (PyInstaller + Inno Setup compiling end-to-end,
   even if the app is a stub)

Acceptance requires the user to personally review the rules cache bootstrap
output and sign off every rule parameter.

The bootstrap run is the single largest Phase 0 task. It cannot be fully
automated at this point because:

- IRS Rev. Procs for the 2026 planning year (retirement limits, inflation
  adjustments) may not have been fully released yet as of the build date;
  some 2025 values may need to be forward-projected with explicit caveat
- OBBBA interpretive Notices are still being released; the bootstrap must
  pin a specific snapshot date and enumerate what is and isn't known
- CA PTET current rule (2026–2030 missed/short June 15 prepayment → 12.5%
  credit reduction, 5-year carryforward, nonrefundable) is controlling and
  must be baked in; this is flagged in §11 of the prompt. See 0004.

## Options considered

### Option A — Phase 0 scaffold only, rules cache is placeholders with TODOs

- Pros: fastest to unblock Phase 1 entry; avoids guessing at values the user
  can authoritatively source
- Cons: violates §18's "populating every rule parameter" requirement;
  delays the real work of rule verification

### Option B — Full rules cache bootstrap, Claude Code fills best current known values with pin cites, user reviews and corrects

- Pros: satisfies §18; forces the rule-verification discipline the user
  signed up for; produces a reviewable artifact
- Cons: requires Claude Code to make initial value choices that may be
  wrong; user must read every parameter

### Option C — Full rules cache bootstrap, Claude Code only fills values for which it can produce a current pin cite from primary authority, leaves gaps explicit

- Pros: same as B plus: refuses to guess; gaps become the user's punch
  list; safer default behavior under §5 Principle 7 ("secondary sources
  never set numbers")
- Cons: slightly more friction at entry; Phase 0 gate may expose more
  "awaiting user input" items than the user expects

## Recommendation

**Option C.** The §5 principle against guessing at numbers is stronger than
the §18 "populate every parameter" language. Claude Code populates a
first-pass rules cache with values it can cite to current primary authority
(govinfo USCODE, eCFR, Rev. Procs on irs.gov, FTB notices). Where a value
requires Rev. Procs not yet released, a current value not yet confirmed, or
is the subject of an open user-judgment decision (PTET current rule; OBBBA
sunset-watch list), the entry is explicit: `status: AWAITING_USER_INPUT`
with the specific authority the value will come from once available. The
user reviews all populated entries and answers all `AWAITING_USER_INPUT`
entries to close the Phase 0 gate.

## Answer

(awaiting user)

## Implementation notes

(to be filled in)

## Follow-ons

- 0002 — Rules cache bootstrap sources and cadence
- 0003 — OBBBA bootstrap snapshot date
- 0004 — CA PTET current rule confirmation
