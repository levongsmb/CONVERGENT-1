"""Phase 2 cross-check protocol.

Runs the `bulk_cross_check` task class against every strategy-library
subcategory whose metadata has null values for priority_score,
entity_applicability, tax_type_impacted, jurisdiction_tags, obbba_touched,
or statutory_cite. Produces normalized metadata by merging LLM responses
back into the category YAML files.

Public entry points:
  - app.cross_check.runner.run_all(today_date, dry_run, real)
  - app.cross_check.null_detection.subcategories_needing_cross_check(library)
  - app.cross_check.merge.apply_cross_check_response(subcategory, response)
  - app.cross_check.audit.AuditLog

CLI:
  python -m app.cross_check --dry-run
  python -m app.cross_check --real --today-date 2026-04-18
"""
