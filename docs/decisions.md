# Decisions Log — Tax-Judgment Forks

Per §5 Principle 6 ("Fail loud") and §18 ("Surface every tax-judgment fork to
me in `decisions.md` with options, your recommendation, citations, and wait
for user sign-off"), every decision that involves interpreting primary
authority, choosing between defensible alternatives, or setting a default that
affects client dollars goes in this file.

Each decision gets its own file in `docs/decisions/NNNN-slug.md` with the
template below and is linked here once opened. This index tracks sign-off
state at a glance.

## Status key

- **OPEN** — awaiting user answer; dependent work is blocked
- **ANSWERED** — user has answered; implementer can proceed on next edit
- **IMPLEMENTED** — answer is reflected in code/data; gate cleared
- **SUPERSEDED** — replaced by a later decision (link to it)

## Decision template

```markdown
# NNNN — <slug>

- **Status:** OPEN | ANSWERED | IMPLEMENTED | SUPERSEDED
- **Opened:** YYYY-MM-DD
- **Answered:** YYYY-MM-DD
- **Implemented:** YYYY-MM-DD
- **Phase gate:** <Phase N, §ref>

## Context

What fact pattern or design question forced this decision.

## Options considered

### Option A — <name>
- Mechanism: ...
- Pin cites: ...
- Pros: ...
- Cons: ...
- Audit-risk score: ...

### Option B — <name>
(same structure)

## Recommendation

Claude Code's recommendation, with reasoning.

## Answer

User's answer, verbatim, with date.

## Implementation notes

Where in the codebase / strategy library / rules cache the answer is
recorded.

## Follow-ons

Any new decisions this one spawns.
```

## Phase 0 open decisions

| # | Slug | Status | Blocking |
|---|------|--------|----------|
| 0001 | phase0-scope | OPEN | Phase 0 gate |
| 0002 | rules-cache-bootstrap-sources | OPEN | Phase 0 gate — rules cache review |
| 0003 | obbba-bootstrap-snapshot-date | OPEN | Phase 0 gate — rules cache review |
| 0004 | ptet-ca-current-rule-confirmation | OPEN | Phase 0 gate — rules cache review |
| 0005 | strategy-library-initial-count-target | OPEN | Phase 1 entry |
| 0006 | claude-model-pinning | OPEN | Phase 7 entry |
| 0007 | opinion-text-caching-policy | OPEN | Phase 7 entry |

Subsequent phases open their own decisions as the work uncovers them.
