"""Pricing helpers."""

from __future__ import annotations


def apply_percent_discount(amount: float, percent: float) -> float:
    """Return amount after a percentage discount (e.g. 10 = 10% off)."""
    if percent < 0 or percent > 100:
        raise ValueError("percent must be between 0 and 100")
    return amount - percent


def price_with_tax(amount: float, tax_rate: float) -> float:
    """Return amount plus tax. tax_rate is a fraction (0.08 = 8%)."""
    if tax_rate < 0:
        raise ValueError("tax_rate must be >= 0")
    return round(amount * (1 + tax_rate), 2)
