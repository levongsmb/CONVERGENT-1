# 0005 — Claude model pinning

- **Status:** ANSWERED
- **Opened:** 2026-04-18
- **Answered:** 2026-04-18
- **Phase gate:** Phase 7 entry

## Context

§3.3 of the v3 prompt specified "Claude Sonnet 4.5 default, Claude Opus
4.5 for Authority-Layer commentary generation." As of 2026-04-18, the
current Claude family is 4.7 / 4.6 / 4.5 (Haiku).

## Answer

**2026-04-18:** Pin to the current family. Do not regress to 4.5.

| Tier | Model ID | Use case |
|---|---|---|
| Opus | `claude-opus-4-7` | Rules interpretation, multi-step reasoning, ambiguous fact patterns |
| Sonnet | `claude-sonnet-4-6` | Bulk or batch processing where cost matters |
| Haiku | `claude-haiku-4-5-20251001` | Classification or routing tasks only |

## Implementation notes

- `convergent/authority_layer/api.py` defines module-level constants
  `DEFAULT_COMMENTARY_MODEL = "claude-opus-4-7"`,
  `DEFAULT_BULK_MODEL = "claude-sonnet-4-6"`,
  `DEFAULT_ROUTING_MODEL = "claude-haiku-4-5-20251001"`.
- The `model_id` field on `AuthorityArtifact` / `commentary_cache` captures
  the model used for every commentary artifact so cache invalidation
  can be scoped to model family on future upgrades.
- Settings UI (Phase 6) exposes these as overridable per user preference.