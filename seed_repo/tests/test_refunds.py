from acme_billing.refunds import compute_refund


def test_full_refund_when_nothing_refunded():
    assert compute_refund(charged=50.0, already_refunded=0.0, request_amount=50.0) == 50.0


def test_partial_refund_respects_remaining():
    # $40 charged, $10 already refunded → $30 left. Request $25 → get $25.
    assert compute_refund(charged=40.0, already_refunded=10.0, request_amount=25.0) == 25.0


def test_cannot_exceed_remaining_balance():
    # $40 charged, $30 already refunded → $10 left. Request $25 → get $10.
    assert compute_refund(charged=40.0, already_refunded=30.0, request_amount=25.0) == 10.0
