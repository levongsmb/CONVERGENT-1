"""§16 persistence — SQLite + encryption.

The three database surfaces:

- **Engagement DB** — one SQLCipher-encrypted SQLite file per engagement, key
  sealed via Windows DPAPI. Lives in `%APPDATA%\\Convergent\\engagements\\`.
- **Rules cache DB** — shared per user, seeded from `rules_cache_bootstrap/`
  at install time, mutated by Statutory Mining refreshes.
- **Authority cache DB** — shared per user, seeded from
  `authority_layer/seed/` at install time.

Phase 0 ships schema definitions only; migrations and encryption wiring land
in Phase 2 (engagement) and Phase 7 (authority).
"""
