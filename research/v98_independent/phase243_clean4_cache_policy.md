# V98 Independent — Clean-4 cache policy

The cache contains only Phase243 training-only original Binance USD-M monthly ZIP files for BTCUSDT, ETHUSDT, BNBUSDT and SOLUSDT, December 2022 through December 2025.

A cache hit is **not** trusted as data validation.

Every consuming workflow must still run `phase243_clean4_source_pipeline.py`, which:
- retrieves the frozen provider .CHECKSUM sidecar;
- verifies each cached ZIP SHA256 against that sidecar;
- reparses the archive under the existing schema/calendar/OHLC/base-quote/taker/residual integrity rules;
- rebuilds canonical CSVs;
- enforces the pre-2026 training firewall.

If a cached ZIP does not match the current frozen source checksum, the acquisition layer redownloads it and validates the replacement before use.

The cache may never contain validation/holdout or 2026+ data.
