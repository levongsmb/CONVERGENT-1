"""Decimal helpers for tax-dollar math.

Per §5 Principle 8: all currency math uses `Decimal` with `ROUND_HALF_UP`
at the penny. Floats are allowed only in statistical / sensitivity modules
where rounding is semantically irrelevant.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, getcontext
from typing import Final

PENNY: Final[Decimal] = Decimal("0.01")
ZERO: Final[Decimal] = Decimal("0")


def setup_decimal_context() -> None:
    """Call once at app startup. Establishes the Decimal context Convergent uses."""
    ctx = getcontext()
    ctx.prec = 28
    ctx.rounding = ROUND_HALF_UP


def to_penny(amount: Decimal | int | float | str) -> Decimal:
    """Round to the nearest cent, ROUND_HALF_UP."""
    if isinstance(amount, float):
        # Floats only as a last resort — convert through string to avoid
        # binary-float artifacts.
        amount = Decimal(str(amount))
    return Decimal(amount).quantize(PENNY, rounding=ROUND_HALF_UP)


def dollars_from_cents(cents: int) -> Decimal:
    return (Decimal(cents) / Decimal(100)).quantize(PENNY, rounding=ROUND_HALF_UP)


def safe_div(num: Decimal, denom: Decimal) -> Decimal:
    if denom == ZERO:
        return ZERO
    return num / denom
