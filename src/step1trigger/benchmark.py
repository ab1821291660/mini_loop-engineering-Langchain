"""Real use case: bug tickets against a small Python billing package.

Tickets are intentionally vague (symptoms only) so a weak config fails and
the improvement loop has something to learn from.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class BugTicket(BaseModel):
    id: str
    title: str
    request: str
    test_path: str = Field(description="pytest path that must pass after the fix")
    expected_edit_substr: str = Field(
        description="Source path fragment that should change (anti-cheat hint)"
    )
    protected_paths: list[str] = Field(
        default_factory=list,
        description="Test files that must not be weakened/deleted",
    )
    failure_hint: str


BENCHMARK: list[BugTicket] = [
    BugTicket(
        id="pricing-discount",
        title="Checkout discounts look wrong",
        request=(
            "ACME-101: Support says percentage discounts on checkout look wrong. "
            "Something in acme_billing pricing is off. Investigate and fix. "
            "Do not change the tests."
        ),
        test_path="tests/test_pricing.py",
        expected_edit_substr="acme_billing/pricing.py",
        protected_paths=["tests/test_pricing.py"],
        failure_hint="Weak config skips tests/ and never runs pytest.",
    ),
    BugTicket(
        id="invoice-total",
        title="Invoice totals undercharge multi-qty lines",
        request=(
            "ACME-204: Finance reports invoice totals are too low when a line "
            "has quantity > 1. Investigate acme_billing invoices and fix. "
            "Do not change the tests."
        ),
        test_path="tests/test_invoices.py",
        expected_edit_substr="acme_billing/invoices.py",
        protected_paths=["tests/test_invoices.py"],
        failure_hint="Weak config guesses without reading failing tests.",
    ),
    BugTicket(
        id="partial-refund",
        title="Partial refunds over-refund",
        request=(
            "ACME-318: Customers sometimes get refunded more than the remaining "
            "balance on a charge. Investigate refunds and fix. "
            "Do not change the tests."
        ),
        test_path="tests/test_refunds.py",
        expected_edit_substr="acme_billing/refunds.py",
        protected_paths=["tests/test_refunds.py"],
        failure_hint="Weak config cannot verify with pytest when shell is disabled.",
    ),
]
