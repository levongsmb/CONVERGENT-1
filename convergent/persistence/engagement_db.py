"""Engagement SQLite schema (SQLCipher at runtime).

Mirrors the §7 canonical data model. All tables carry `created_at` and
`updated_at`. Every numeric column that holds tax dollars uses `NUMERIC` so
SQLite preserves full Decimal precision when paired with SQLAlchemy's
``TypeDecorator`` adapter in Phase 2.

This module is schema-only in Phase 0. Session management, encryption key
derivation (DPAPI seal), and migrations arrive in Phase 2.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
)

metadata = MetaData()

# --- Top-level engagement ---------------------------------------------------

engagement = Table(
    "engagement",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("name", String(200), nullable=False),
    Column("tax_year", Integer, nullable=False),
    Column("planning_horizon_years", Integer, nullable=False),
    Column("engagement_type", String(40), nullable=False),
    Column("responsible_cpa", String(120), nullable=False),
    Column("partner_reviewer", String(120)),
    Column("due_date", DateTime),
    Column("billing_code", String(40)),
    Column("scope_text", Text),
    Column("jurisdiction_scope", String(60), nullable=False),  # FED | FED_CA | FED_MULTI
    Column("wealth_transfer_in_scope", Boolean, nullable=False, default=False),
    Column("locked", Boolean, nullable=False, default=False),
    Column("locked_at", DateTime),
    Column("last_run_at", DateTime),
    Column("rules_cache_snapshot_id", String(36)),
    Column("strategy_library_version", String(64)),
    Column("active_scenario_id", String(36)),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)

# --- Intake §6A -------------------------------------------------------------

taxpayer = Table(
    "taxpayer",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("legal_name", String(200), nullable=False),
    Column("preferred_name", String(200)),
    Column("dob", DateTime, nullable=False),
    Column("ssn_encrypted", String(200), nullable=False),  # SQLCipher + app-layer redaction
    Column("filing_status", String(20), nullable=False),
    Column("state_of_residence", String(2), nullable=False),
    Column("county", String(80)),
    Column("citizenship_status", String(40), nullable=False),
    Column("is_primary", Boolean, nullable=False, default=True),
    Column("health_insurance_source", String(40)),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)

family_member = Table(
    "family_member",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("relationship", String(40), nullable=False),
    Column("legal_name", String(200), nullable=False),
    Column("dob", DateTime, nullable=False),
    Column("dependent_federal", Boolean, nullable=False, default=False),
    Column("dependent_state", Boolean, nullable=False, default=False),
    Column("earned_income", Numeric(18, 2)),
    Column("fulltime_student", Boolean, nullable=False, default=False),
    Column("disabled", Boolean, nullable=False, default=False),
    Column("available_as_trust_beneficiary", Boolean, nullable=False, default=False),
    Column("employable_in_family_business", Boolean, nullable=False, default=False),
    Column("notes", Text),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)

income_source = Table(
    "income_source",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("source_type", String(40), nullable=False),
    Column("payer", String(200)),
    Column("owner", String(40), nullable=False),  # taxpayer | spouse | joint | entity:<id> | minor:<id>
    Column("annual_amount", Numeric(18, 2), nullable=False),
    Column("character_tag", String(40)),
    Column("state_source", String(2)),
    Column("recurring", Boolean, nullable=False, default=True),
    Column("predicted_character_alt", String(40)),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)

entity = Table(
    "entity",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("entity_type", String(40), nullable=False),
    Column("legal_name", String(200), nullable=False),
    Column("ein_encrypted", String(200)),
    Column("date_of_formation", DateTime),
    Column("date_of_s_election", DateTime),
    Column("state_of_formation", String(2)),
    Column("states_of_operation_json", JSON),
    Column("naics_code", String(8)),
    Column("is_sstb", Boolean),
    Column("accounting_method", String(20)),
    Column("tax_year_end", String(5)),  # MM-DD
    Column("formation_narrative", Text),
    Column("facts_json", JSON, nullable=False),  # gross receipts history, W-2 wages, §199A UBIA, etc.
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)

entity_ownership = Table(
    "entity_ownership",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("entity_id", String(36), ForeignKey("entity.id"), nullable=False),
    Column("owner_kind", String(20), nullable=False),  # taxpayer | family_member | trust | entity
    Column("owner_ref", String(36), nullable=False),
    Column("pct", Numeric(9, 6), nullable=False),
    Column("as_of", DateTime, nullable=False),
    Column("voting", Boolean, nullable=False, default=True),
)

retirement_plan = Table(
    "retirement_plan",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("entity_id", String(36), ForeignKey("entity.id")),
    Column("plan_type", String(40), nullable=False),
    Column("plan_year", Integer),
    Column("current_balance", Numeric(18, 2)),
    Column("facts_json", JSON, nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)

balance_sheet_item = Table(
    "balance_sheet_item",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("category", String(40), nullable=False),  # liquid | real_estate | closely_held | insurance | debt
    Column("subcategory", String(40)),
    Column("facts_json", JSON, nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)

estate_posture = Table(
    "estate_posture",
    metadata,
    Column("engagement_id", String(36), ForeignKey("engagement.id"), primary_key=True),
    Column("facts_json", JSON, nullable=False),  # documents on file, exemption consumed, DSUE, GST allocation
    Column("updated_at", DateTime, nullable=False),
)

election_in_force = Table(
    "election_in_force",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("entity_id", String(36), ForeignKey("entity.id")),
    Column("election_code", String(40), nullable=False),  # §754, §444, §1361_ESBT, §645, ...
    Column("effective_date", DateTime),
    Column("parameters_json", JSON),
    Column("created_at", DateTime, nullable=False),
)

# --- Ingestion §6B ----------------------------------------------------------

ingested_document = Table(
    "ingested_document",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("upload_timestamp", DateTime, nullable=False),
    Column("filename", String(400), nullable=False),
    Column("sha256", String(64), nullable=False),
    Column("file_type", String(10), nullable=False),
    Column("source_attestation", String(40), nullable=False),
    Column("classified_form", String(20)),
    Column("classified_tax_year", Integer),
    Column("classified_jurisdiction", String(10)),
    Column("classified_subtype", String(20)),
    Column("classifier_confidence", Numeric(5, 4)),
    Column("taxpayer_identity_matched", Boolean),
    Column("parser_output_id", String(36)),
    Column("review_status", String(30), nullable=False),
    Column("reviewer_notes", Text),
)

prior_year_snapshot = Table(
    "prior_year_snapshot",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("tax_year", Integer, nullable=False),
    Column("filing_status", String(20)),
    Column("federal_totals_json", JSON, nullable=False),
    Column("state_totals_json", JSON, nullable=False),
    Column("entities_json", JSON, nullable=False),
    Column("carryovers_json", JSON, nullable=False),
    Column("elections_in_effect_json", JSON, nullable=False),
    Column("audit_exposure_json", JSON, nullable=False),
    Column("source_document_ids_json", JSON, nullable=False),
    Column("created_at", DateTime, nullable=False),
)

reconciliation_entry = Table(
    "reconciliation_entry",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("field_path", String(200), nullable=False),
    Column("manual_value", String(200)),
    Column("parsed_value", String(200)),
    Column("delta_amount", Numeric(18, 2)),
    Column("resolution", String(20)),  # accept_parsed | accept_manual | split | unresolved
    Column("resolved_by", String(120)),
    Column("resolved_at", DateTime),
    Column("notes", Text),
)

# --- Goals §6C --------------------------------------------------------------

goals_inventory = Table(
    "goals_inventory",
    metadata,
    Column("engagement_id", String(36), ForeignKey("engagement.id"), primary_key=True),
    Column("objectives_json", JSON, nullable=False),
    Column("constraints_json", JSON, nullable=False),
    Column("risk_appetite_json", JSON, nullable=False),
    Column("custom_preferences_json", JSON),
    Column("sign_off_timestamp", DateTime),
    Column("sign_off_by", String(120)),
)

# --- Scenarios §8 / §14 -----------------------------------------------------

scenario = Table(
    "scenario",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("ordinal", Integer, nullable=False),  # 0 = baseline; 1..N = A..E
    Column("label", String(40), nullable=False),
    Column("strategy_bundle_json", JSON, nullable=False),
    Column("result_json", JSON, nullable=False),
    Column("narrative", Text),
    Column("cost_estimate_json", JSON, nullable=False),
    Column("compliance_flags_json", JSON, nullable=False),
    Column("monte_carlo_seed", Integer, nullable=False),
    Column("solver_configuration_json", JSON, nullable=False),
    Column("input_hashes_json", JSON, nullable=False),  # intake, goals, rules cache snapshot, library version
    Column("created_at", DateTime, nullable=False),
)

# --- Authority artifacts §12A ----------------------------------------------

authority_artifact = Table(
    "authority_artifact",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("scenario_id", String(36), ForeignKey("scenario.id")),
    Column("artifact_type", String(20), nullable=False),  # FOOTNOTE | FLAG | PITFALL | COMMENTARY
    Column("topic", String(100), nullable=False),
    Column("severity", String(10)),  # BLOCK | WARN | INFO — flags only
    Column("body", Text, nullable=False),
    Column("citations_json", JSON, nullable=False),
    Column("freshness_date", DateTime, nullable=False),
    Column("prompt_hash", String(64)),
    Column("authority_snapshot_id", String(36), nullable=False),
    Column("created_at", DateTime, nullable=False),
)

# --- Memo artifacts ---------------------------------------------------------

memo_artifact = Table(
    "memo_artifact",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("scenario_ids_json", JSON, nullable=False),
    Column("format", String(10), nullable=False),  # docx | pdf
    Column("path", String(500), nullable=False),
    Column("sha256", String(64), nullable=False),
    Column("generated_at", DateTime, nullable=False),
    Column("generator_version", String(40), nullable=False),
)

cost_estimate = Table(
    "cost_estimate",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("scenario_id", String(36), ForeignKey("scenario.id"), nullable=False),
    Column("strategy_id", String(80), nullable=False),
    Column("evaluate_low", Numeric(18, 2), nullable=False),
    Column("evaluate_base", Numeric(18, 2), nullable=False),
    Column("evaluate_high", Numeric(18, 2), nullable=False),
    Column("implement_low", Numeric(18, 2), nullable=False),
    Column("implement_base", Numeric(18, 2), nullable=False),
    Column("implement_high", Numeric(18, 2), nullable=False),
    Column("maintain_annual_low", Numeric(18, 2), nullable=False),
    Column("maintain_annual_base", Numeric(18, 2), nullable=False),
    Column("maintain_annual_high", Numeric(18, 2), nullable=False),
    Column("complexity_multiplier", Numeric(6, 3), nullable=False),
    Column("third_party_notes", Text),
)

# --- Audit + overrides ------------------------------------------------------

override_log = Table(
    "override_log",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("target_kind", String(40), nullable=False),  # parsed_field | rule_cache | strategy_flag | compliance_flag
    Column("target_ref", String(200), nullable=False),
    Column("old_value", Text),
    Column("new_value", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("by_user", String(120), nullable=False),
    Column("at", DateTime, nullable=False),
)

audit_trail = Table(
    "audit_trail",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("engagement_id", String(36), ForeignKey("engagement.id"), nullable=False),
    Column("event_type", String(60), nullable=False),
    Column("payload_json", JSON, nullable=False),
    Column("at", DateTime, nullable=False),
    Column("by_user", String(120)),
)
