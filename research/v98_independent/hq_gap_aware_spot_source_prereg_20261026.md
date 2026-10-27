# V98 Independent HQ — separate gap-aware spot provenance contract (2026-10-26)

Status: PREREGISTERED SOURCE-ONLY, BEFORE HQ CODE OR ANY HQ ECONOMIC RESULTS. This is a NEW provenance protocol, **not** a repair or reversal of the frozen `spot_perp_source_only.py` rejection. The strict 100-archive, complete-grid spot source remains permanently rejected. No strategy is selected by source outcome.

## Immutable scope
- Binance publisher official **spot** monthly 1h ZIP and publisher SHA256 .CHECKSUM for BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, Dec-2022 warmup + Jan-2023 through Dec-2024 TRAINING ONLY (25 months per asset, 100 archives).
- No 2025 holdout, no 2026+, XRP, Phase083, V14/V15/V99 internals, Frozen or paper; no economic PnL, backtest, orders or external benchmark.
- Source-only expected calendar: 18,288 UTC hours per asset, 73,152 asset-hours total.
- All 100 ZIPs must verify against corresponding publisher SHA256 sidecars; ZIP member exact, timestamps strictly increasing, unique, on 1h UTC grid, numeric OHLC and quote volume finite and valid. Any unexpected timestamp, duplicate, checksum mismatch, invalid OHLC, out-of-calendar timestamp, non-UTF8, or additional missing hour => FAIL.
- Known provider-authenticated defects: exactly four asset-hours at **2023-03-24T13:00:00Z**, one per asset, previously independently verified. Those four are marked `observed=0` with EMPTY OHLC/quote fields, **never filled, interpolated, forward-filled, priced or included in indicators**. All 73,148 observed hours must remain exactly as published. If the publisher revises these four to genuine provider-authenticated bars, FAIL under this frozen contract pending separate provenance decision, not a silent source upgrade.
- The gap-aware CSV is a calendar/index + explicit observation mask, **NOT** a complete spot OHLC source. A downstream feature at decision t is eligible only if every required historical spot bar is observed and its timestamp <=t. The gap hour and every rolling window touching it must be ineligible; no decision can use an absent value. A masked gap is not a zero return or zero volume. Never mix 2025 into fitting.
- Two independent deterministic builds from the same verified raw archives must produce identical bytes and SHA256; receipt records ZIP checksums, observed/missing counts, exact missing timestamps, canonical digest, source-only status and explicit no-PnL/no-holdout flags.
- Separate deterministic synthetic fixtures test missingness, checksum failure, duplicate/out-of-grid rejection, lookback masking and future mutation invariance. Fixture pass is **not** official source acceptance.

## Next gates (not automatically granted)
1. Run source-only pipeline on official 100 archives in a separately authorized V98-only runner and independently reconcile publisher SHA, observed counts and missingness.
2. Only after source acceptance, preregister a genuinely distinct seven-slot **complete** spot/perp information hypothesis and its execution/cost gates BEFORE looking at economic results. Rejected HP/HO and previous strategies stay rejected.
3. Full USD-M native funding and fee/slippage physical books, t close -> t+1 open, 30-cell survival, independent settlement, chronological 2023/24 economic folds, positive optional-sleeve marginal contributions, severe/supersevere, drawdown, turnover, concentration, tails. Freeze before separate 2025 holdout. No live trading.
