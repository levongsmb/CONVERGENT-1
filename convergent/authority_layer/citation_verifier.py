"""§12A.8 Citation Verifier.

After the Authority Layer composes commentary, parse every numerical claim
(dollar amount, percentage, date, year) and verify each appears in the
retrieved primary authority. If not, reject and re-prompt with narrower
retrieval. Three rejections in a row surface as
``commentary_verification_failure``.

Phase 0: stub. Full implementation in Phase 7.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NumericalClaim:
    value_str: str
    span_start: int
    span_end: int
    kind: str  # USD | PCT | DATE | YEAR | COUNT


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    unverified_claims: tuple[NumericalClaim, ...]
    rejected_reason: str | None = None


def extract_numerical_claims(body: str) -> tuple[NumericalClaim, ...]:
    """Phase 0 stub."""
    raise NotImplementedError("Phase 0 stub — Citation Verifier lands in Phase 7.")


def verify_against_sources(body: str, source_texts: tuple[str, ...]) -> VerificationResult:
    """Phase 0 stub."""
    raise NotImplementedError("Phase 0 stub — Citation Verifier lands in Phase 7.")
