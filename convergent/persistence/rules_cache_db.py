"""Rules cache schema.

The rules cache is populated by the Statutory Mining subsystem (§12A.14)
and consumed by every tax computation module. It is shared per-user (not
per-engagement) and snapshot-pinned for reproducibility.

Every rule value carries:

- Its jurisdiction (federal, state code, multistate framework)
- Its authority pin cite (source URL + retrieved_at)
- Its effective date window
- The tax year(s) it applies to
- A verification_status field (bootstrapped | verified_by_cpa | needs_review |
  stale)

Phase 0: schema + bootstrap loader. Statutory Mining refresh wiring lands in
Phase 7.
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
    UniqueConstraint,
)

metadata = MetaData()

rules_cache_snapshot = Table(
    "rules_cache_snapshot",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("created_at", DateTime, nullable=False),
    Column("label", String(80), nullable=False),  # "bootstrap-2026-04-18" or "refresh-2026-05-02-a"
    Column("sources_polled_json", JSON, nullable=False),
    Column("diff_summary_json", JSON),
    Column("approved_by_user", Boolean, nullable=False, default=False),
    Column("approved_at", DateTime),
    Column("approved_by", String(120)),
    Column("notes", Text),
)

rule_parameter = Table(
    "rule_parameter",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("snapshot_id", String(36), ForeignKey("rules_cache_snapshot.id"), nullable=False),
    Column("jurisdiction", String(10), nullable=False),  # FED | CA | NY | ...
    Column("code_section", String(80), nullable=False),
    Column("sub_parameter", String(100), nullable=False),
    Column("tax_year", Integer, nullable=False),
    Column("effective_from", DateTime, nullable=False),
    Column("effective_to", DateTime),
    Column("value_numeric", Numeric(20, 6)),
    Column("value_text", Text),
    Column("unit", String(40)),  # USD | PCT | RATIO | DATE | ENUM
    Column("authority_kind", String(40), nullable=False),  # IRC | REG | REV_PROC | REV_RUL | NOTICE | PL | RTC | FTB_NOTICE
    Column("authority_citation", String(200), nullable=False),
    Column("authority_url", String(500)),
    Column("retrieved_at", DateTime, nullable=False),
    Column("verification_status", String(30), nullable=False),
    # bootstrapped | verified_by_cpa | needs_review | awaiting_user_input | stale
    Column("verified_by", String(120)),
    Column("verified_at", DateTime),
    Column("notes", Text),
    UniqueConstraint(
        "snapshot_id",
        "jurisdiction",
        "code_section",
        "sub_parameter",
        "tax_year",
        name="uq_rule_parameter_coord",
    ),
)

obbba_notice = Table(
    "obbba_notice",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("snapshot_id", String(36), ForeignKey("rules_cache_snapshot.id"), nullable=False),
    Column("notice_number", String(40), nullable=False),  # e.g., "2026-01"
    Column("released_at", DateTime, nullable=False),
    Column("title", String(400), nullable=False),
    Column("affected_code_sections_json", JSON, nullable=False),
    Column("summary", Text, nullable=False),
    Column("full_text_url", String(500), nullable=False),
    Column("cached_text_path", String(500)),
    Column("verification_status", String(30), nullable=False),
)

listed_transaction = Table(
    "listed_transaction",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("snapshot_id", String(36), ForeignKey("rules_cache_snapshot.id"), nullable=False),
    Column("designation_citation", String(200), nullable=False),  # Notice 2023-34, etc.
    Column("label", String(200), nullable=False),
    Column("pattern_summary", Text, nullable=False),
    Column("strategy_library_ids_blocked_json", JSON, nullable=False),  # IDs that would be suppressed
    Column("designated_at", DateTime, nullable=False),
    Column("still_designated", Boolean, nullable=False, default=True),
)

reportable_transaction = Table(
    "reportable_transaction",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("snapshot_id", String(36), ForeignKey("rules_cache_snapshot.id"), nullable=False),
    Column("category", String(40), nullable=False),  # loss | confidential | contractual_protection | transaction_of_interest
    Column("designation_citation", String(200), nullable=False),
    Column("label", String(200), nullable=False),
    Column("pattern_summary", Text, nullable=False),
    Column("designated_at", DateTime, nullable=False),
    Column("still_designated", Boolean, nullable=False, default=True),
)
