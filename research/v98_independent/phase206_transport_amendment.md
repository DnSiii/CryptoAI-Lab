# V98 Independent — Phase206 transport amendment

Date frozen: 2026-10-01
Status: **TRANSPORT-ONLY AMENDMENT / NO ECONOMIC RESULTS INSPECTED**

## Why this amendment is admissible

The original Phase206 preregistration froze the economic object (realized perpetual funding), universe, training cutoff, causal alignment, eight-spec grid, costs, metrics and promotion discipline. It did not freeze `fapi.binance.com` as the sole transport. The later acquisition utility selected Binance's public USD-M `fundingRate` REST endpoint as transport.

GitHub Actions run 36894852391 failed during the first acquisition step with HTTP 451 from that REST host. No funding payload was received, no funding value was inspected, and no Phase206 signal, return, correlation, trade, threshold outcome or PnL was computed.

Binance's official `binance/binance-public-data` repository documents `https://data.binance.vision/` as Binance Data Collection for public market data, with monthly files and sidecar `.CHECKSUM` files. The USD-M `fundingRate` archive represents the same realized funding object with fields `calc_time`, `funding_interval_hours`, and `last_funding_rate`.

Therefore Phase206 may retry acquisition through the official Binance archive as a transport substitution before any result exists. This is **not** source shopping: provider (Binance), market (USD-M perpetuals), symbols, timestamps, realized funding semantics, training window and hypothesis remain unchanged.

## Frozen transport-v2 contract

- Provider: Binance only.
- Host: `https://data.binance.vision`.
- Dataset path: `data/futures/um/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{YYYY}-{MM}.zip`.
- Symbols: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- Months: 2022-01 through 2025-12 only.
- Every downloaded ZIP must match its official `.CHECKSUM` sidecar SHA256.
- Accepted schema is exactly the archive funding schema: `calc_time`, `funding_interval_hours`, `last_funding_rate` (case-insensitive canonical matching only; no semantic field substitution).
- Output retains `calc_time` as funding timestamp, `last_funding_rate` as realized funding rate, and `funding_interval_hours` as published interval.
- No missing month may be silently skipped. No interpolation or imputation.
- All retained timestamps must be `< 2026-01-01T00:00:00Z`.
- Reacquire the complete archive twice and require byte-identical canonical per-symbol CSV hashes.
- Preserve source ZIP and checksum hashes in the manifest.

## Scientific firewall

This amendment does not change the Phase206 signal grid, direction, costs, hold periods, folds, promotion criteria, or any economic parameter. It does not authorize validation/final holdout, V16, V99, post-hoc asset selection, threshold expansion, inversion, or rescue.

If the official archive cannot satisfy this frozen transport-v2 contract, Phase206 closes as `FAIL_DATA_NO_ALPHA`. Only a successful deterministic acquisition may authorize execution of the already-preregistered Phase206 economic evaluator.
