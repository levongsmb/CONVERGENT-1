"""`authority.query()` — Phase 0 API surface.

Every module that needs authority commentary talks to this function, never
to Claude directly. The implementation in Phase 7 will:

1. Retrieve relevant authority from the cache via `topic`
2. Sanitize `scenario_context` per §16.5 (strip PII, bucket amounts)
3. Compose a Jinja2 prompt from the appropriate template in `prompts/`
4. Memoize on (topic, scenario_context_hash, artifact_type, max_length,
   authority_snapshot_id)
5. Call the Anthropic SDK for commentary (unless a memoized hit)
6. Run the Citation Verifier against the response
7. Return a typed AuthorityArtifact

§6B.4's `document_classifier.classify()` is a **separate** interface and
does not share this API surface, even though both call the Anthropic SDK.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Final


# -----------------------------------------------------------------------
# Model pinning per Decision 0005 (2026-04-18).
#
# The v3 prompt specified Sonnet 4.5 / Opus 4.5. User confirmed 2026-04-18
# to pin the 4.7 / 4.6 / 4.5 (Haiku) family instead — the 4.5 tier is
# superseded. Settings UI (Phase 6) exposes these as overridable per
# user preference; AuthorityArtifact.model_id captures the exact model
# used for every commentary artifact so cache invalidation can be
# scoped to model family on future upgrades.
# -----------------------------------------------------------------------

DEFAULT_COMMENTARY_MODEL: Final[str] = "claude-opus-4-7"
DEFAULT_BULK_MODEL: Final[str] = "claude-sonnet-4-6"
DEFAULT_ROUTING_MODEL: Final[str] = "claude-haiku-4-5-20251001"


class ArtifactType(str, Enum):
    FOOTNOTE = "FOOTNOTE"
    FLAG = "FLAG"
    PITFALL = "PITFALL"
    COMMENTARY = "COMMENTARY"


class Severity(str, Enum):
    BLOCK = "BLOCK"
    WARN = "WARN"
    INFO = "INFO"


@dataclass(frozen=True)
class Citation:
    kind: str  # IRC | REG | REV_RUL | REV_PROC | NOTICE | CASE | FTB_NOTICE | FTB_LR | PL
    citation: str
    pin: str | None = None  # specific subsection / line / page
    url: str | None = None
    retrieved_at: datetime | None = None


@dataclass(frozen=True)
class AuthorityArtifact:
    topic: str
    artifact_type: ArtifactType
    body: str
    citations: tuple[Citation, ...]
    freshness_date: datetime
    authority_snapshot_id: str
    prompt_hash: str | None = None
    severity: Severity | None = None  # flags only
    model_id: str | None = None


@dataclass(frozen=True)
class ScenarioContext:
    """Sanitized, PII-stripped fact bucket supplied to the authority query.

    §16.5: names / SSN / EIN / addresses are never populated here. Dollar
    amounts are bucketed to order-of-magnitude bands ("$1M-$5M" etc.) before
    this struct is constructed. The constructor does not enforce this — the
    `pii_sanitizer` module is the single checkpoint that converts a raw
    `IntakeRecord` into a `ScenarioContext`.
    """

    entity_types: tuple[str, ...]
    revenue_band: str | None
    state: str
    filing_status: str | None
    relevant_code_sections: tuple[str, ...]
    extra: dict[str, Any] = field(default_factory=dict)


def query(
    topic: str,
    scenario_context: ScenarioContext,
    artifact_type: ArtifactType,
    *,
    max_length: int = 500,
    citation_only: bool = False,
) -> AuthorityArtifact:
    """Retrieve or compose an authority artifact. Phase 0 stub."""
    raise NotImplementedError("Phase 0 stub — Authority Layer lands in Phase 7.")
