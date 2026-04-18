# Changelog

Phase-by-phase build log per §18. Each phase gets a subsection. Only
user-visible behavior changes are recorded here — incidental refactors and
test additions live in git history.

## [Unreleased]

### Phase 0 — Repo scaffold, rules cache bootstrap (in progress)

- **Added:** repository structure per `docs/REPO_LAYOUT.md`
- **Added:** `pyproject.toml` with pinned dependencies (numpy 2.1.3, scipy
  1.14.1, pandas 2.2.3, pydantic 2.9.2, NiceGUI 2.7.0, plotly 5.24.1,
  SQLAlchemy 2.0.36, anthropic 0.39.0, pytesseract 0.3.13, pdfplumber
  0.11.4, camelot 0.11.0, python-docx 1.1.2, reportlab 4.2.5, cryptography
  43.0.3, argon2-cffi 23.1.0, pyinstaller 6.11.1 for dev)
- **Added:** `docs/decisions.md` index + initial decision files 0001–0004
- **Added:** `OPEN_QUESTIONS.md` with the Phase 0 blocking queue
- **Added:** `BACKLOG_V2.md` seed
- **Added:** SQLite schema scaffolding for engagement, rules cache,
  authority cache (persistence package not yet functional)
- **Added:** Statutory Mining subsystem scaffold with per-source stubs
- **Added:** Rules cache bootstrap skeleton with first-pass YAML files
  (values pending user sign-off per §18 acceptance gate)
- **Added:** Strategy Library `MANIFEST.yaml` scaffold (category
  directories only; strategy YAMLs land in Phase 1)
- **Added:** Authority Layer skeleton with `authority.query()` stub,
  Pitfall Library YAML seed, prompt template placeholders
- **Added:** Installer skeleton — PyInstaller spec, Inno Setup script,
  vendor directory for tesseract/ghostscript (binaries not yet bundled)
- **Gate status:** AWAITING USER SIGN-OFF on rules cache parameters (see
  `rules_cache_bootstrap/README.md`)

Phase 0 is **not complete**. Phase 1 cannot begin until the user signs off
every rule parameter in `rules_cache_bootstrap/` per §18.

## Format

We follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) with
sections: **Added**, **Changed**, **Deprecated**, **Removed**, **Fixed**,
**Security**, and the Convergent-specific **Gate status**.
