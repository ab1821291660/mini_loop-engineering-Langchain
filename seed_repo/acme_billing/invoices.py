"""Invoice model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LineItem:
    description: str
    unit_price: float
    quantity: int = 1

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise ValueError("quantity must be >= 1")
        if self.unit_price < 0:
            raise ValueError("unit_price must be >= 0")


@dataclass
class Invoice:
    currency: str = "USD"
    lines: list[LineItem] = field(default_factory=list)

    def add_line(self, item: LineItem) -> None:
        self.lines.append(item)

    def total(self) -> float:
        """Sum of line totals, rounded to cents."""
        raw = sum(line.unit_price for line in self.lines)
        return round(raw, 2)
