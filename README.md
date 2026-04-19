# Convergent — Strategic Tax Optimization Suite

**Status:** Phase 3b in progress (per-category evaluator build). Not yet deployable for engagement work.

Convergent is a Python-based, locally-run, multi-entity tax planning and
scenario optimization application for closely-held business owners and their
advisors. See the full build specification in `docs/PROMPT_V3.md` (the consolidated
prompt that governs this build).

## Platform

Windows 11 only. No macOS or Linux build is planned. Minimum target spec:
Windows 11 22H2+, 16 GB RAM, 20 GB free disk, x64.

## Build prerequisites (developer)

- Windows 11 with Python 3.12 installed from python.org (not Windows Store, not WSL)
- Visual Studio Build Tools 2022 with the "Desktop development with C++" workload
  (required by some dependencies to build wheels)
- Inno Setup 6 for installer compilation
- Tesseract 5.x Windows build (bundled inside the installer at build time)
- Ghostscript 10.x Windows build (bundled inside the installer at build time)

## Developer setup

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
python -m playwright install chromium
```

## Runtime prerequisites (end user)

Microsoft Edge WebView2 runtime (pre-installed on Windows 11 22H2+).
The installer verifies presence and installs silently if missing.

Currently: only ongoing paid dependency is an Anthropic API key (used by the
Authority Layer). Stored in Windows Credential Manager via `keyring`.

## Build status

See `PROGRESS.md` for the current gate state and the next task.
G0–G7 are signed; G8 (STATE_SALT) is backfilled per the 2026-04-19
governance reconciliation. Phase 3b continues on the MANIFEST category
sequence. Governance, sign-off workflow, and the Commit-and-Push Policy
are documented in `CLAUDE.md`; per-gate history is in `CHANGELOG.md`;
per-category sign-offs live under
`__strategy_library/subcategories/<CATEGORY>_EVALUATORS_SIGNOFF.md`.

Outstanding ◐/☐ rows in `rules_cache_bootstrap/review_checklist.md`
remain open but do not block current Phase 3b evaluator work.

## Repository layout

See `docs/REPO_LAYOUT.md`.

## Governance docs

- `docs/decisions.md` — every tax-judgment fork surfaced during the build, with
  options, recommendation, citations, and user sign-off status
- `OPEN_QUESTIONS.md` — questions the user must answer before a blocked phase
  can continue
- `CHANGELOG.md` — phase-by-phase build log
- `BACKLOG_V2.md` — features and strategies surfaced during the build that
  are deferred past Phase 11
