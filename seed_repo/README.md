# Acme Billing
Tiny Python billing helpers used by the loop-engineering demo.


# Run the seed repo's pytest suite directly (all three should FAIL until fixed)
```bash
python -m pytest -q
uv run python -m pytest seed_repo/tests -q
uv run python -m pytest seed_repo/tests/test_pricing.py -q   # single ticket
```
Known open tickets live in the issue tracker the coding agent receives.


##三张工单与 seed 缺陷：：症状型工单 —— 不给公式，逼 agent 调查
Ticket	           症状	          根因文件
pricing-discount   百分比折扣错    pricing.py：amount - percent
invoice-total      多数量少计费    invoices.py：忽略 quantity
partial-refund     部分退款超额    refunds.py：未 clamp 剩余额度

