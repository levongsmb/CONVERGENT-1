"""Authority cache schema.

Backs §12A.2 — statutory text, regulation text, Rev. Rul./Proc./Notice
records, court opinion metadata (and full text where public-domain and
cached), FTB Notices, mapping tables.

Phase 0: schema only. Bootstrap loaders and Claude-API-backed commentary
generation land in Phase 7.
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
    String,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()

authority_snapshot = Table(
    "authority_snapshot",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("created_at", DateTime, nullable=False),
    Column("label", String(80), nullable=False),
    Column("sources_polled_json", JSON, nullable=False),
    Column("notes", Text),
)

statute = Table(
    "statute",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("snapshot_id", String(36), ForeignKey("authority_snapshot.id"), nullable=False),
    Column("code", String(10), nullable=False),  # IRC | CA_RTC | NY_TL | ...
    Column("section", String(40), nullable=False),
    Column("subsection", String(40)),
    Column("body", Text, nullable=False),
    Column("effective_from", DateTime, nullable=False),
    Column("effective_to", DateTime),
    Column("source_url", String(500), nullable=False),
    Column("retrieved_at", DateTime, nullable=False),
    UniqueConstraint("snapshot_id", "code", "section", "subsection", name="uq_statute_coord"),
)

regulation = Table(
    "regulation",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("snapshot_id", String(36), ForeignKey("authority_snapshot.id"), nullable=False),
    Column("cite", String(80), nullable=False),  # e.g., "1.199A-1(b)(4)"
    Column("status", String(20), nullable=False),  # final | temporary | proposed
    Column("body", Text, nullable=False),
    Column("effective_from", DateTime),
    Column("td_number", String(40)),
    Column("source_url", String(500), nullable=False),
    Column("retrieved_at", DateTime, nullable=False),
    UniqueConstraint("snapshot_id", "cite", "status", name="uq_reg_coord"),
)

published_guidance = Table(
    "published_guidance",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("snapshot_id", String(36), ForeignKey("authority_snapshot.id"), nullable=False),
    Column("kind", String(20), nullable=False),  # REV_RUL | REV_PROC | NOTICE | ANNOUNCEMENT | AOD | PLR | IRM | FTB_NOTICE | FTB_LR
    Column("citation", String(60), nullable=False),  # "Rev. Rul. 2026-5", "Notice 2026-12", "FTB Notice 2026-1"
    Column("title", String(400), nullable=False),
    Column("released_at", DateTime, nullable=False),
    Column("summary", Text, nullable=False),
    Column("body", Text),
    Column("source_url", String(500), nullable=False),
    Column("retrieved_at", DateTime, nullable=False),
    UniqueConstraint("snapshot_id", "kind", "citation", name="uq_guidance_coord"),
)

court_opinion = Table(
    "court_opinion",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("snapshot_id", String(36), ForeignKey("authority_snapshot.id"), nullable=False),
    Column("court", String(20), nullable=False),  # TC | CFC | DIST | CIR | SCOTUS | STATE
    Column("parties", String(400), nullable=False),
    Column("citation", String(200), nullable=False),
    Column("opinion_date", DateTime, nullable=False),
    Column("result", String(60), nullable=False),
    Column("topics_json", JSON, nullable=False),
    Column("summary", Text, nullable=False),
    Column("body_cached", Boolean, nullable=False, default=False),
    Column("body", Text),
    Column("source_url", String(500), nullable=False),
    Column("retrieved_at", DateTime, nullable=False),
    UniqueConstraint("snapshot_id", "citation", name="uq_opinion_coord"),
)

mapping_section_to_guidance = Table(
    "mapping_section_to_guidance",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("snapshot_id", String(36), ForeignKey("authority_snapshot.id"), nullable=False),
    Column("code", String(10), nullable=False),
    Column("section", String(40), nullable=False),
    Column("guidance_id", String(36), ForeignKey("published_guidance.id"), nullable=False),
    Column("relevance", String(20), nullable=False),  # controlling | interpretive | related
)

mapping_strategy_to_authority = Table(
    "mapping_strategy_to_authority",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("snapshot_id", String(36), ForeignKey("authority_snapshot.id"), nullable=False),
    Column("strategy_id", String(80), nullable=False),
    Column("authority_kind", String(20), nullable=False),  # statute | regulation | guidance | opinion
    Column("authority_id", String(36), nullable=False),
    Column("role", String(20), nullable=False),  # primary | supporting | contra
)

commentary_cache = Table(
    "commentary_cache",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("topic", String(100), nullable=False),
    Column("artifact_type", String(20), nullable=False),
    Column("prompt_hash", String(64), nullable=False),
    Column("snapshot_id", String(36), ForeignKey("authority_snapshot.id"), nullable=False),
    Column("body", Text, nullable=False),
    Column("citations_json", JSON, nullable=False),
    Column("model_id", String(60), nullable=False),
    Column("generated_at", DateTime, nullable=False),
    UniqueConstraint("topic", "artifact_type", "prompt_hash", "snapshot_id", name="uq_commentary_memo"),
)
