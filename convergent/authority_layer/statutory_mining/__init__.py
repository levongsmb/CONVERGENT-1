"""§12A.14 Statutory Mining subsystem.

Polls primary-authority public URLs on a scheduled cadence and keeps the
rules cache and authority cache current.

Source-specific polling modules live in `sources/`:

- `irs.py` — irs.gov/newsroom (Notices, Announcements), Listed/Reportable
  indices
- `treasury.py` — regs.gov Treasury/IRS dockets
- `ustaxcourt.py` — ustaxcourt.gov/decisions
- `ftb.py` — ftb.ca.gov news and legal-rulings
- `govinfo.py` — USCODE bulk data (authoritative IRC text), CFR Title 26
  monthly snapshots, Federal Register
- `ecfr.py` — eCFR diffs for regulation parts already cached
- `federal_register.py` — daily FR JSON feed

Phase 0: scaffolding, source stubs, bootstrap CLI entry point. Full polling
lands in Phase 7.
"""
