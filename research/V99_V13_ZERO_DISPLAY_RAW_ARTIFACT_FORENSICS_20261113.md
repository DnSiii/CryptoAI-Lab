# V13 paper zero-display forensic evidence — 2026-11-13

Source: original GitHub Actions run 42032849643, uploaded artifact `paper-v13-opportunities-42032849643` (artifact ID 13418245331, SHA-256 archive digest 4614f3bf500125eddba16d44a5c79e8e65016cfbb28bf88a2ad114553a2aaa01). This is **read-only evidence**, not a rewritten paper or verified repair.

The original `reports/paper_v13_ledger.json` contains 688 decisions and 1,439 adjustments. Exactly **one** adjustment has `order_value_brl <= 0`:

- decision index 681, adjustment index 0, timestamp `2026-11-04T19:00:00+00:00`
- `symbol=BTCUSDT`, `action_code=reduce_short`, `order_side=buy`, `order_value_brl=0.0`
- `previous_weight=-0.04735247`, `new_weight=-0.04735225`, delta `+0.00000022`
- `capital_before_brl=10123.63`, `execution_price=80314.0`
- proxy `abs(delta)*capital_before_brl = 0.0022271986 BRL`, below half a cent. **This is only a proxy**, not the unrounded executed notional or proof of a fill. The artifact adjustment does not contain `order_value_brl_unrounded`.

The failure in the original run is `scripts/verify_paper_cycle_v13.py` line 74, `RuntimeError: movimentação sem valor executado`. The failure occurs after all paper generation jobs; the history/publication gates are skipped. A later branch verifier explicitly accepts only positive unrounded notionals strictly below 0.005 BRL that display as zero, but the original artifact has no unrounded field, so it **cannot pass this stricter verifier without separately recovered execution evidence**.

**Next necessary proof:** inspect the frozen paper runner's original arithmetic, original per-event pre-round notional (if recorded elsewhere), and historical source bytes; independently reconstruct notional without changing any trades, then test positive subcent values, zero execution, NaN/Inf, negative values, inconsistent direction, and boundary values (0.005). Only after a successful full GitHub Actions verification should publication resume. Keep Frozen, baseline, and holdout untouched. No economic promotion, no real orders.
