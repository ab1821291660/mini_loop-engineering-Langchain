from acme_billing.invoices import Invoice, LineItem


def test_single_line_respects_quantity():
    inv = Invoice()
    inv.add_line(LineItem("Widget", unit_price=10.0, quantity=3))
    assert inv.total() == 30.0


def test_multiple_lines():
    inv = Invoice()
    inv.add_line(LineItem("A", unit_price=5.0, quantity=2))
    inv.add_line(LineItem("B", unit_price=7.5, quantity=1))
    assert inv.total() == 17.5


def test_rejects_bad_quantity():
    try:
        LineItem("bad", unit_price=1.0, quantity=0)
        assert False, "expected ValueError"
    except ValueError:
        pass
