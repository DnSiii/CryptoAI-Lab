# V99 source-of-truth separation audit — 2026-11-14 22:44 UTC

Scope: read-only GitHub connector inspection of branch `research/v99-r106-native-all-regime-engine`, not a new backtest or market provenance certificate.

## Direct evidence
- `scripts/verify_paper_cycle_v13.py` blob `22f4754c5300a4e1970547198fc6017431b1f314` checks PAPER_ONLY, real_orders_enabled=false, state/snapshot equality, asset reconciliation, and strict subcent rounding. A zero displayed order is accepted only if finite positive raw notional <0.005, nonzero weight delta, and Python two-decimal round matches; nonfinite and missing raw fail closed.
- Branch `reports/paper_v13_snapshot.json` blob `71886cdf289f93181687e6a9d838145290b36d39` has latest_data_timestamp `2026-08-14T03:00:00+00:00` and 8 forward hours. This is a **branch working-tree snapshot, NOT the live published paper-results branch**; do not use it to declare current live paper stale.
- Branch `reports/paper_data_sync_v13.json` blob `4d5887cae88cd3ce0561cf7e73a4283ed6231015` was generated 2026-08-14 and uses `OFFICIAL_CHECKSUMMED_DAILY_ARCHIVES`; the current verifier instead requires `OFFICIAL_ARCHIVES_PLUS_PUBLIC_CLOSED_KLINES_AND_FUNDING_REST`. Thus running the current verifier against these historical checked-in reports is not a valid proof of today's paper freshness. Workflow restores durable state and synchronizes new market data before verifying.
- GitHub Actions run [43632832128](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/43632832128) reports success for paper safety/freshness, historical preservation, durable publication and dashboard refresh steps. A green workflow is not independent verification of public HTTP-served dashboard content or economic execution provenance.
- C1 rejection documented in `research/V99_R106_C1_COMPLETE_ENGINE_TRAIN_REJECTION_20261016.md`: severe -20.7856%, 1/5 folds; supersevere -3.4081%, 2/5 folds. No promotion.

## Next falsifiable actions
1. Read the **published** paper-results state, ledger, and sync from the same immutable commit, reconcile forward-hour monotonicity and exact adjustment raw notionals; keep frozen history unchanged.
2. Check actual GitHub Pages HTTP response and visible stale/research-only notice; distinguish successful deploy workflow from served site.
3. Audit exchange receipt capture timestamps vs event timestamps and source fees/funding/fills; do not treat public market klines as execution receipts.
4. Only then preregister a genuinely distinct full-system TRAIN-only architecture; preserve validation from 2023-10-01 and final holdout from 2024-01-18.

No orders, economic run, strategy promotion, or modification of V16/V99 Frozen, paper-results, champion, or holdout in this audit.
