"""PII sanitization at the Anthropic API boundary per §16.5.

No client PII ever leaves the machine except inside Anthropic API calls. At
that boundary, the fact pattern is sanitized:

- Names, SSNs, EINs, addresses: removed (replaced with typed placeholders)
- Specific dollar amounts: bucketed to order-of-magnitude bands

This module is the single gatekeeper. Every path that constructs a
`ScenarioContext` goes through `sanitize_for_authority()`. The regression
suite (§17.3) includes adversarial cases ensuring no bypass.

Phase 0: API surface + bucket definitions. Real sanitizer lands in Phase 7.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from convergent.authority_layer.api import ScenarioContext


REVENUE_BANDS: tuple[tuple[Decimal, Decimal, str], ...] = (
    (Decimal("0"), Decimal("100000"), "<$100K"),
    (Decimal("100000"), Decimal("250000"), "$100K-$250K"),
    (Decimal("250000"), Decimal("1000000"), "$250K-$1M"),
    (Decimal("1000000"), Decimal("5000000"), "$1M-$5M"),
    (Decimal("5000000"), Decimal("25000000"), "$5M-$25M"),
    (Decimal("25000000"), Decimal("100000000"), "$25M-$100M"),
    (Decimal("100000000"), Decimal("10000000000"), ">$100M"),
)


def bucket_amount(amount: Decimal) -> str:
    for low, high, label in REVENUE_BANDS:
        if low <= amount < high:
            return label
    return ">$100M"


def sanitize_for_authority(intake_record_like: object) -> "ScenarioContext":
    """Phase 0 stub — full implementation in Phase 7."""
    raise NotImplementedError("Phase 0 stub — sanitizer lands in Phase 7.")


def assert_no_pii(context: "ScenarioContext") -> None:
    """Adversarial check used by the regression suite. Phase 0 stub."""
    raise NotImplementedError("Phase 0 stub — enforcement lands in Phase 7.")
