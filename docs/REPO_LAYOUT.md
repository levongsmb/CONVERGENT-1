# Repository layout

Convergent is a single Python package (`convergent`) plus supporting assets.
Every module boundary in the build prompt (§§6–15) maps to a sub-package.

```
convergent/
  __main__.py                    # CLI entry point
  config.py                      # paths, environment, app directories
  ingestion/                     # §6B prior-return ingestion
    classifier.py
    reviewer_queue.py
    reconciler.py
    parsers/
      f1040.py
      f1120s.py
      f1065.py
      f1120.py
      f1041.py
      f706_709.py
      ca_540_100s_565_568_541.py
      states/                    # NY, NJ, MA, etc.
  intake/                        # §6A household/entity wizard
    schema.py                    # IntakeRecord Pydantic model
    wizard_views.py              # NiceGUI page components
  goals/                         # §6C goals and risk appetite
    schema.py                    # GoalsInventory
    weights.py                   # priority rank -> objective weight vector
  engine/                        # §8 / §14 scenario engine
    convergence.py               # §8.1 fixed-point loop
    baseline.py                  # Scenario 0 construction
    scenario_generator.py        # A/B/C/D/E bundles
    sensitivity.py               # Monte-Carlo-flavored sensitivity
    tax/
      federal_ordinary.py
      federal_amt.py
      federal_capital.py
      niit.py
      seca_fica.py
      california.py
      multi_state.py
      transfer.py
      recapture.py
      excise.py
  optimizer/                     # §14 optimization
    bundle_mip.py                # PuLP/CBC bundle composition
    params_continuous.py         # SLSQP parameter tuning
    diversity.py                 # scenario-diversity enforcement
  strategies/                    # §12 strategy quantification modules
    __init__.py
    compensation/
    retirement/
    qbi_199a/
    entity_selection/
    qsbs_1202/
    trusts_income_shifting/
    trusts_wealth_transfer/
    charitable/
    estate_gift_gst/
    real_estate_depreciation/
    installment_deferral/
    credits/
    capital_gains_losses/
    international/
    state_salt/
    accounting_methods/
    loss_limit_navigation/
    sale_transaction/
    miscellaneous/
    compliance_and_procedural/
  authority_layer/               # §12A live authority + commentary
    api.py                       # authority.query() entry point
    cache.py                     # SQLite authority cache
    citation_verifier.py
    compliance_flags.py
    pitfall_engine.py
    sunset_watch.py
    pii_sanitizer.py
    statutory_mining/
      scheduler.py
      bootstrap.py
      sources/
        irs.py
        treasury.py
        ustaxcourt.py
        ftb.py
        govinfo.py
        ecfr.py
        federal_register.py
    prompts/
      footnote.jinja
      flag.jinja
      pitfall.jinja
      commentary.jinja
    connectors/
      optional/                  # disabled by default; user opts in
  cost_of_advice/                # §15
    rate_card.py
    complexity_adjust.py
  memo/                          # §10 memo generator
    generator.py
    templates/
  persistence/                   # §16 SQLite + encryption
    engagement_db.py
    rules_cache_db.py
    authority_cache_db.py
    sqlcipher_key.py             # DPAPI-sealed key derivation (Win32)
    export_cvg.py                # portable .cvg export/import
    backup.py
  ui/                            # §9 dashboard + intake
    app.py                       # NiceGUI entry point
    design_system.py             # colors, typography, chart defaults
    views/
      intake.py
      dashboard.py
      authority_dock.py
      memo_preview.py
      settings.py
  util/
    decimal_tax.py               # Decimal helpers, ROUND_HALF_UP penny math
    derivation_tree.py
    logging.py                   # structlog config
    time_windows.py              # SOL, §1202 clock, §1400Z clock, etc.

strategy_library/                # §12.1 YAML — not code
  MANIFEST.yaml
  compensation/
  retirement/
  ...  (one file per strategy, loaded at runtime)

authority_layer/                 # authority layer runtime assets (prompts, seed cache)
  pitfalls.yaml
  listed_transactions.yaml
  reportable_transactions.yaml
  seed/                          # bootstrapped primary-authority cache packaged into installer

rules_cache_bootstrap/           # Phase 0 deliverable — first-pass rules cache
  README.md                      # review workflow for user sign-off
  federal/                       # Per-section YAMLs with exact statutory text sources + cite
  california/
  review_checklist.md

tests/
  golden/                        # 30 golden engagement scenarios (Phase 5)
  unit/
  integration/

scripts/
  bootstrap_rules_cache.py       # Phase 0 runner — populates rules_cache_bootstrap/
  build_installer.ps1            # PyInstaller + Inno Setup driver (Windows)
  verify_rules_cache.py          # cross-foot + citation spot-check helper

installer/
  convergent.iss                 # Inno Setup script
  pyinstaller.spec               # PyInstaller onefolder spec
  runtime_hooks/
  vendor/                        # bundled tesseract.exe, gswin64c.exe, tessdata/
  README.md

docs/
  PROMPT_V3.md                   # full build specification (the pasted prompt, for reference)
  REPO_LAYOUT.md                 # this file
  decisions.md                   # tax-judgment forks surfaced during the build
  INSTALL.md
  USER_MANUAL.md                 # filled in at Phase 10
  decisions/
    0001-phase0-scope.md         # one file per decision
    ...
```
