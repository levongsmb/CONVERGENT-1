# SIGNOFF — `<target_yaml_filename>`

**Reviewer:** `<initials>`
**Review date:** `<YYYY-MM-DD>`
**Target YAML:** `<filename>.yaml`

## Purpose

Parameter-level accountability per Decision 0007. Each parameter row in
the target YAML is recorded here as `signed_off`, `corrected`, or
`needs_review`. When the target YAML changes, this file must be updated.

## Status key

- **signed_off** — value in YAML is correct as populated
- **corrected** — reviewer edited the YAML; note the delta below
- **needs_review** — reviewer flagged for re-sourcing; Claude Code
  cannot advance dependent work until this is resolved

## Parameters

Copy one block per parameter from the target YAML. For large tables
(e.g., bracket tables), a single block covering the entire table is
acceptable if the reviewer signs off the whole table.

### `<sub_parameter name>`

- **Coordinate:** `<tax_year / filing_status / regime / etc.>`
- **YAML value:** `<value>`
- **Authority cited:** `<citation>`
- **Status:** signed_off | corrected | needs_review
- **If corrected — new value:**
- **If corrected — reason:**
- **If needs_review — reason:**

---

## Overall sign-off

When every parameter block above is `signed_off` or `corrected`, add the
line below.

```
Reviewed and approved: <YYYY-MM-DD> — <initials>
```
