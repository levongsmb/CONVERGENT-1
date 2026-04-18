# G0 — Hot-Swappable Configuration Architecture Sign-Off

Firm: SMB CPA Group, PC
Reviewer of record: Levon Galstian, CPA (License 146973)
Build spec section: 0.5 and Section 8 (Sign-Off Gates)

This gate certifies that the hot-swappable configuration architecture is in
place and that Phase 1a (Client Scenario Schema) may begin.

## Deliverables produced under G0

| # | Deliverable | Path |
|---|-------------|------|
| 1 | Top-level config manifest | `config/VERSION.yaml` |
| 2 | Task-class to model routing | `config/models.yaml` |
| 3 | Config directory layout matching spec Section 0.5 | `config/rules_cache/2026/{federal,california}/`, `config/authorities/2026/state/`, `config/forms/{federal,california}/`, `config/prompts/`, `config/report_templates/`, `config/cross_check_schemas/` |
| 4 | LLM router (the only place model strings are resolved) | `app/config/router.py` |
| 5 | Rules cache loader | `app/config/rules.py` |
| 6 | Authority loader with per-year id uniqueness | `app/config/authorities.py` |
| 7 | Form metadata loader with applicability-year enforcement | `app/config/forms.py` |
| 8 | Jinja2 prompt renderer (strict undefined) | `app/config/prompts.py` |
| 9 | Pre-commit config validator | `app/config/validate.py` |
| 10 | Reference cross-check prompt externalized | `config/prompts/cross_check_subcategory.j2` |
| 11 | Reference authority file | `config/authorities/2026/irc_sections.yaml` |
| 12 | Reference form file | `config/forms/california/3804.yaml` |

## Reference authority coverage

`config/authorities/2026/irc_sections.yaml` includes twelve IRC sections
selected for use by Phase 3a MVP evaluators and Phase 2 cross-check
retrievals:

- §199A (QBI, OBBBA-amended)
- §1202 (QSBS, OBBBA-amended with pre- and post-OBBBA split metadata)
- §164 (SALT cap with full sunset metadata through 2030)
- §461 (EBL, OBBBA-permanent)
- §151 (personal exemption and §151(f) senior deduction)
- §1062 (qualified farmland four-year installment election, new under OBBBA)
- §174 and §174A (foreign R&E amortization and domestic R&E expensing)
- §139L (qualified lender agricultural interest exclusion, new under OBBBA)
- §168 (bonus depreciation permanent restoration)
- §2010 ($15M basic exclusion permanent)
- §1411 (NIIT reference for §1202 interaction)

## Reference form coverage

`config/forms/california/3804.yaml` populated with the SB 132 regime for
taxable years 2026-2030:

- Election filed with Form 565 / 568 / 100S on original timely-filed return
- Calendar-year due date March 15; fiscal-year due on original entity return
- June 15 minimum prepayment (CA FTB 3893) = greater of 50% prior-year PTET or $1,000
- Shortfall consequence = 12.5% credit reduction on shortfall amount, measured at return filing date
- Election remains valid despite shortfall
- Primary authority: SB 132 (Ch. 17, Stats. 2025); new RTC sections enacted by SB 132; FTB Form 3804 Instructions; FTB PTET FAQ

## Architectural guarantees verified

1. Router is the only location where model strings appear. Task classes
   (`complex_reasoning`, `bulk_cross_check`, `classification`, `memo_polish`)
   are the stable API surface; model strings are fluid in `config/models.yaml`.
2. Escalation target references resolve (no orphan task-class names).
3. Every YAML under `config/` parses cleanly and declares `config_version`
   where applicable.
4. Authority IDs are unique within a given tax year across all authority
   files under `config/authorities/<year>/`.
5. Form metadata declares form number, latest revision, and jurisdiction.
6. Prompt templates live only in `config/prompts/`, rendered by the
   central `app.config.prompts.render()` entry point. Jinja environment
   uses `StrictUndefined` so missing template variables fail loudly.
7. Validator (`python -m app.config.validate`) passed.

## Consumption pattern for Phases 1-5

Evaluators and services read from config. Examples:

```python
from app.config.router import get_llm_config
from app.config.rules import get_rule
from app.config.authorities import get_authority
from app.config.forms import get_form
from app.config.prompts import render

cfg = get_llm_config("bulk_cross_check")
qbi_params = get_rule("federal/qbi_199a", year=2026)
auth_199a = get_authority("199A", year=2026)
form_3804 = get_form("3804", year=2026, jurisdiction="california")
prompt = render("cross_check_subcategory", parent_category="QBI_199A", sub=sub, today_date="2026-04-18")
```

No model string, no rate, no threshold, no form number, no statutory cite,
and no prompt text lives in Python source.

## Migration note

`rules_cache_bootstrap/federal/*.yaml` and `rules_cache_bootstrap/california/*.yaml`
were populated and signed off under the prior Phase 0 gate. Phase 1 of this
build migrates those files into `config/rules_cache/2026/federal/` and
`config/rules_cache/2026/california/` without duplication. Legacy
`rules_cache_bootstrap/` remains in place until migration completes, then
is removed.

## Prior repository scaffolding

Directories `convergent/`, `strategy_library/`, `authority_layer/`, and
`tests/` contain scaffolding from the prior build. Under this master
build spec ("All prior discussion threads are superseded by this
document"), new work proceeds under `app/`, `config/`, and
`__strategy_library/`. Prior directories remain for reference and will
be reconciled or removed during later phases as their content is either
migrated or obsoleted.

## Sign-off

- [ ] Router task classes resolve to the intended models
- [ ] Escalation paths (`bulk_cross_check` → `complex_reasoning`,
      `classification` → `bulk_cross_check`) are correct for firm policy
- [ ] Config validator output "config/ validation passed" accepted
- [ ] Reference authority file covers the sections required for Phase 3a MVP
- [ ] Reference form file matches SB 132 regime parameters signed off under
      Decision 0004
- [ ] No contractions, no emojis, no hype, no marketing language appear in
      any generated content

Signed: __________________________________
Date: __________________________________
