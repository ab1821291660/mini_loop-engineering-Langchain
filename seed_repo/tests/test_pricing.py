from acme_billing.pricing import apply_percent_discount, price_with_tax


def test_ten_percent_off_hundred():
    assert apply_percent_discount(100.0, 10) == 90.0


def test_zero_percent_is_noop():
    assert apply_percent_discount(49.99, 0) == 49.99


def test_full_discount():
    assert apply_percent_discount(25.0, 100) == 0.0


def test_tax_unchanged():
    assert price_with_tax(100.0, 0.08) == 108.0
