# V98 Independent — preregistered static-exposure diagnostic (2026-11-02)

**Purpose:** Diagnose whether the repeated failure of composed V98 candidates reflects avoidable strategy churn or a genuine market/cost constraint. This is an **internal exposed-training control**, NOT a V98 candidate, alpha search, selection rule, superiority benchmark or trading authorization. Freeze these controls before observing any results. No tuning after results.

**Data:** Clean-4 Binance USD-M BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT 1h, December 2022 warmup through 2025-12-31 inclusive; 27,048 hours, 13,524 native funding calendar/rate events, conservative source-native hourly mark envelope. No 2026+, quarantined XRP, Phase083, V14/V15/V99, paper or Frozen.

**Six predetermined books:** all cash (0); static BTC 0.80 long; static ETH 0.80 long; static BNB 0.80 long; static SOL 0.80 long; static equal-weight 0.20 long each. Set initial positions at first next-hour open following t=743 (first 2023 trading hour); **never rebalance** until terminal close. No shorts, no hidden leverage, no selection from these results.

**Ledger:** reuse existing V98 independent physical accounting arithmetic only (not any rejected strategy signal): next-hour open fills, 10% maintenance, hourly adverse candle checks, no hidden leverage, signed funding with conservative mark bounds, terminal close. 3 *illustrative* one-way all-in cost tiers 10/20/35 bps, both funding/fill orders, six books = **36** full 27,048-hour cells. Record full cash, CAGR, annual returns, max drawdown, turnover, funding, costs, positive days, and physical survival. A failed cell is reported as failed, never cosmetically repaired.

**Independent check:** recompute all-cash and equal-weight base ledger independently from source rows and cash arithmetic, detect tampered cash, verify no 2026/holdout. Report 2023/2024/2025 training-only baseline results without claiming a deployable V98. This controls for the economic hurdle before committing another novel seven-slot hypothesis. Exact 13,524 original funding settlement marks and account-executable costs are still missing, so all economic results remain illustrative and nonvalidated.
