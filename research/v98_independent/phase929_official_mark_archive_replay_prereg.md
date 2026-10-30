# V98 Independent Phase929 — Official mark archive provenance replay (pre-result)

Scope: `research/v98-independent-zero` only. Clean-4 BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT, Binance USD-M hourly, 2022-12 warmup and 2023-01 through 2024-12 training. No 2025/2026, XRP, old Phase083 holdout, or external engine benchmarks.

Hypothesis: the official Binance Vision monthly 1h `markPriceKlines` ZIP and `.CHECKSUM` can authenticate conservative funding-settlement mark bounds where the restricted futures API returned HTTP 451. Verify all 100 mark archives and all 100 native funding archives afresh within the SAME GitHub Actions run; verify 9,144 timestamp-matched settlement bounds and their checksum digest. Preserve the official-origin receipts even on failure. A 1h high for positive funding debit and low for negative funding credit is deliberately conservative for long positions, NOT a claim to have authenticated an instantaneous API mark. No substitute or fabricated mark is acceptable.

Decision: PASS only if Phase797's predeclared official-origin/geometry/calendar/native SHA pins and 9,144-event checks all pass. Otherwise FAIL-CLOSED with reason, no PnL and no promotion. This run is SOURCE ONLY; never invoke a funded ledger, never use validation/holdout data. Do not modify any V16/V99 files or state.

Next, and only after source success, synchronize the N-only code and launch the preregistered 90-cell 2023/2024 training matrix with the same-run source gate, report all failures, and separately validate before benchmarking external engines.
