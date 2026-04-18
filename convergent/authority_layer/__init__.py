"""§12A Dynamic Authority Layer.

Scaffold only in Phase 0. See:

- `api.query()` — single entry point every other module uses
- `statutory_mining/` — §12A.14 sources, scheduler, bootstrap
- `pii_sanitizer` — §16.5 outbound sanitization at the Anthropic API boundary
- `citation_verifier` — §12A.8 numerical-claim verification
- `compliance_flags` — §12A.11 flag engine (BLOCK/WARN/INFO)
- `pitfall_engine` — §12A.10 pitfall matching
- `sunset_watch` — §12A.13 OBBBA sunset-watch evaluator
- `prompts/` — Jinja2 prompt templates for each artifact type

Full implementation lands in Phase 7.
"""
