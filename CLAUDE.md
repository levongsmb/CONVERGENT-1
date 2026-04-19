# CLAUDE.md — Convergent

## PROJECT PURPOSE

Convergent is a Python-based, locally-run, multi-entity tax planning and
scenario optimization application for closely-held business owners and their
advisors. It is a deterministic rules engine (not a generative tool) with an
Anthropic-API-backed Authority Layer used only for cross-checking and
commentary. The build is governed by the consolidated specification in
`docs/PROMPT_V3.md` (also called the "master build spec").

## TECH STACK

- Language: Python 3.12 (strict — `>=3.12,<3.13`)
- Target platform: Windows 11 22H2+ only (x64). No macOS / Linux / WSL builds.
- Core libs: `pydantic==2.9.2`, `numpy`, `scipy`, `pandas`, `pulp`
  (MIP optimization), `sqlalchemy` + `pysqlcipher3` (encrypted persistence),
  `nicegui` + `pywebview` + `plotly` (UI), `anthropic==0.39.0` (Authority
  Layer only), `ruamel.yaml` (round-trip-safe cross-check merges),
  `pdfplumber` / `camelot` / `pytesseract` (document ingestion),
  `reportlab` / `python-docx` / `openpyxl` / `docx2pdf` (document output),
  `keyring` (Windows Credential Manager), `jinja2` (prompts — StrictUndefined).
- Dev: `pytest`, `pytest-asyncio`, `pytest-cov`, `playwright`, `ruff`,
  `mypy` (strict), `pyinstaller`.
- Installer: Inno Setup 6; bundles Tesseract 5 and Ghostscript 10.
- LLM model pinning (per Decision 0005, `config/models.yaml`):
  `complex_reasoning` → `claude-opus-4-7`;
  `bulk_cross_check` → `claude-sonnet-4-6`;
  `classification` → `claude-haiku-4-5-20251001`;
  `memo_polish` → `claude-opus-4-7`.

## ARCHITECTURE OVERVIEW

The repo currently hosts two coexisting build layers. The older `convergent/`
package (per `docs/REPO_LAYOUT.md`) is the v3 scaffolding from the original
spec — intake, ingestion, engine, optimizer, strategies, authority_layer,
memo, persistence, UI, util. In Phase 0 (G0, 2026-04-18) a new hot-swappable
configuration architecture was added under `app/` and `config/`, superseding
prior discussion threads per Decision 0010. New build work lives under
`app/` (scenario models, evaluators, cross-check, per-category tests),
`config/` (versioned rules_cache, authorities, forms, prompts, models
manifest), and `__strategy_library/` (40-category MANIFEST with 616
subcategories and per-category `_SIGNOFF.md` companions). Evaluators are
auto-discovered Pydantic-v2-driven modules that read config via a
`ConfigRulesAdapter` and return `StrategyResult` objects with quantified
`TaxImpact`. The Authority Layer runs only against a local cache of primary
authorities populated by the `statutory_mining` scheduler. The UI is a local
NiceGUI app served through a pywebview window.

## CONVENTIONS

- Exact-version dependency pinning. Any upgrade requires re-running the full
  golden-scenario suite (§18 of the spec).
- Penny math: `Decimal` with `ROUND_HALF_UP`. See `convergent/util/decimal_tax.py`.
- Every module that touches tax parameters pulls from `config/rules_cache/`
  via `app/config/rules.py` — never hardcode bracket / threshold / rate
  values.
- Every Phase / Gate ends with a sign-off companion: files named
  `*_SIGNOFF.md`. Phase work does not advance until the user signs off.
- Citations: authority YAMLs under `config/authorities/<tax_year>/` are the
  single source of truth. `applies_to_tax_years` enforcement on forms.
- Jinja2 prompts use `StrictUndefined` — template variables must be provably
  present.
- Evaluators self-register by `SUBCATEGORY_CODE`; adding a new evaluator means
  dropping a file into `app/evaluators/<CATEGORY>/<CODE>.py` and a test file
  into `app/tests/evaluators/<CATEGORY>/test_<code>.py`.
- Cross-check merges use `ruamel.yaml` round-trip-safe semantics to preserve
  user-signed inline citations.
- `ruff` lint rules: `E, F, W, I, N, UP, B, SIM, RUF` with `line-length = 100`
  and `ignore = ["E501"]`.
- `mypy` strict mode on.
- Testing: tests live under `app/tests/` (new build) and `tests/unit/` (legacy
  scaffolding). Marker taxonomy in `pyproject.toml`:
  `golden`, `authority`, `ui`, `windows`.

## STANDING RULES

- Never add a macOS/Linux build target. Explicitly out of scope per §3.1.
- Never auto-update dependencies. Pinning is deliberate.
- Never invoke Anthropic API calls outside the Authority Layer.
- Never bypass the Gate sign-off workflow. If `G<N>_SIGNOFF.md` is not signed,
  the next phase is blocked.
- Never hardcode tax parameters; always read through `app/config/rules.py`.
- Do not commit secrets. The API key is stored in Windows Credential Manager
  via `keyring`, never on disk.
- Respect `docs/decisions/` — every tax-judgment fork has a numbered decision.
- Additive-only for `BACKLOG_V2.md` during Phases 0–11; strategy ideas go
  there, not into silent inclusion.

## HOW TO RUN / TEST

Developer setup (Windows PowerShell):
```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
python -m playwright install chromium
```

Run tests:
```
pytest app/tests/              # new build — evaluators, scenarios, cross-check
pytest tests/                  # legacy scaffolding tests (if any)
pytest -m golden               # slow end-to-end scenarios (Phase 5+)
pytest -m authority            # requires ANTHROPIC_API_KEY
pytest -m ui                   # requires Playwright browsers
```

Config validation:
```
python -m app.config.validate
```

Cross-check protocol (Phase 2):
```
python -m app.cross_check --today-date 2026-04-18 --dry-run
python -m app.cross_check --today-date 2026-04-18 --real   # spends API $
```

CLI entry points (declared in `pyproject.toml`):
- `convergent`                 — main app
- `convergent-bootstrap`       — statutory mining bootstrap
- `convergent-mine`            — one-off statutory mining run

Installer build (Windows):
```
.\scripts\build_installer.ps1
```

## Commit and Push Policy

Claude Code must commit and push at every logical stopping point without
waiting to be asked. A logical stopping point is any of:

1. **Gate close.** Any G-numbered gate signature lands. Commit + push
   immediately after the signature commit.
2. **Category complete.** A Phase 3b category (sequence_order 1-40) has
   all evaluators, all tests green, and SIGNOFF drafted. Commit + push
   before requesting user signature.
3. **Evaluator batch complete.** A batch of 5+ new evaluators written,
   all tests passing, registry auto-discovery verified. Commit + push.
4. **Substantive refactor complete.** Any cross-cutting change to
   _base.py, _registry.py, config/, or scenario/ that touches 3+ files
   and leaves the suite green. Commit + push.
5. **Governance fix.** Any CHANGELOG backfill, SIGNOFF correction, or
   documentation reconciliation. Commit + push.
6. **End of session.** Regardless of state. If there are uncommitted
   changes at session close, stage and commit them with a WIP message,
   then push.

Pre-commit checklist — run silently before every commit:

- [ ] pytest app/tests/ passes (or explicitly note "WIP: tests failing" in commit message)
- [ ] git status shows only files I intended to change
- [ ] Commit message has title under 60 chars + 2-4 bullet body
- [ ] No Co-Authored-By trailer unless user instructs

Push rule: `git push origin main` after every commit. Local-only commits
are not durable state. The 2026-04-18 incident proved local chat + local
commits can be lost simultaneously.

Self-review gate before pushing: ask internally "would a fresh session
reading only CHANGELOG + PROGRESS + the latest SIGNOFF understand what
just happened?" If no, update those files in the same commit.

Anti-patterns (do not do):
- Bundling unrelated changes into one commit
- Pushing without running tests
- Skipping CHANGELOG/PROGRESS updates for "small" changes
- Waiting for user approval on routine commits that fit this policy
  (user approval still required for commit messages on substantive
   changes affecting evaluator behavior, tax positions, or governance
   state — when in doubt, ask)

Commit now, commit often. Every push to origin/main is cheap insurance.
