"""Refund helper."""

from __future__ import annotations


def compute_refund(
    charged: float,
    already_refunded: float,
    request_amount: float,
) -> float:
    """Return how much can still be refunded for this request."""
    if charged < 0 or already_refunded < 0 or request_amount < 0:
        raise ValueError("amounts must be >= 0")
    if already_refunded > charged:
        raise ValueError("already_refunded cannot exceed charged")
    return charged
