# V99 R106 — independent native accounting firewall (2026-10-16)

**Status: DATA_ONLY/HOLD; NO PROMOTION.** Research branch only. V16 Frozen, V99 Frozen, paper-results, champion, sealed validation [2023-10-01, 2024-01-18) and final holdout >=2024-01-18 are immutable. No real orders.

## Independent evidence and interpretation

Official C1/C2 TRAIN reports and their original-open oracles verified *the original formula*, not a self-financing position/cash ledger. The original formula charges turnover on changes of **target weights** while re-applying unchanged target weights every hour without charging for the intervening price-drift rebalance. The claimed ROI therefore is not a valid self-financing portfolio PnL. The C1 and C2 economic candidates remain permanently rejected and cannot be retuned or promoted.

Local offline reconstruction of four SHA-pinned original TRAIN journals found 13,046 identifiable hours out of 16,055, leaving 3,009 underidentified hours when the raw BTC/ETH open-price source is absent. A constructive 168-hour counterexample demonstrates that different price paths can produce the same original journal gross equation yet different true turnover. In this cycle, the provided offline audit suite was re-executed after restoring its C2 module dependency: 26 self-financing tests, 2 replay-verifier tests, 3 analytic-fee tests and 6 non-identifiability tests passed (37 total). These are **software and forensic results, not profitable strategy results**.

## Mandatory next gates

1. Integrate independently tested self-financing share/cash ledger on this research branch; validate exact transaction fees on actual traded notional, including hourly target restoration after drift. Reject non-UTC, noncontiguous and >=2023-10-01 source rows *before* any economic calculation.
2. Restore original canonical BTC/ETH hourly TRAIN opens from GitHub Actions cache; replay **unchanged rejected C2 targets** solely to quantify historical accounting defect, not to create a candidate or choose parameters. Compare two independent share/cash oracles, five chronological folds, 3x2 regimes, severe/supersevere, tails, drawdown and benchmark envelope. Never open sealed validation or final holdout.
3. Do not preregister or run another economic engine until the accounting gate passes and a scientifically independent mechanism is justified ex ante. Native OKX fee tier, position-specific settled funding and real fills remain unproven, so no simulated ROI is exchange-certified net return.

Original immutable evidence: Actions 38916067167 (C1) and 38919570898 (C2). Offline audit bundle: V99_R106_NATIVE_IDENTIFIABILITY_20261016_1552_BRT.zip. No dashboard champion change authorized.
