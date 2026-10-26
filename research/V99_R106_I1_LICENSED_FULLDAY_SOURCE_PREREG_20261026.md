# V99 I1 — bounded licensed non-sample full-day original quote source check (preregistered 2026-10-26)

**SOURCE_ONLY/HOLD — NO PROMOTION.** Direct critical-path source acquisition check, not a new alpha search, economic TRAIN, or trading execution. The existing Tardis scope probe only verifies two gzip bytes; it cannot prove any BTC/ETH option rows, valid native displayed size, exchange/local clocks or a complete gzip day. This test addresses that precise missing evidence, without buying data or publishing licensed bytes.

## Fixed protocol before implementation
- One fixed non-free **TRAIN** day only: **2022-06-15 UTC** (not the free first of month); Deribit `quotes/2022/06/15/OPTIONS.csv.gz`. No validation >=2023-10-01, final holdout, Frozen, paper/results, champion, or orders.
- Require existing `TARDIS_API_KEY` Actions secret. If absent, return machine-readable `BLOCKED_NO_AUTHENTICATED_ENTITLEMENT` without network access; never treat CI success as market availability. Do not log key, request URL credentials, or store/archive/upload original paid CSV/gzip.
- Use HTTPS authenticated streaming, decompress entire gzip, enforce maximum **512 MiB compressed** and **8,000,000 CSV rows** and 12-minute request budget; abort cleanly on limit/HTTP error/invalid gzip. A truncated stream or gzip failure is a BLOCK, not coverage.
- Required original columns: `exchange,symbol,timestamp,local_timestamp,bid_price,ask_price,bid_amount,ask_amount`. Verify Deribit venue, local-arrival day boundary and nondecreasing capture order, event <= arrival, BTC/ETH option instrument names and positive finite bid<ask, sizes>0. Compute compressed original SHA-256 and per-asset counts without emitting raw data.
- Only `SOURCE_ONE_DAY_FIELDS_OBSERVED_NOT_LIFECYCLE` when gzip fully consumed and both BTC and ETH have valid two-sided put quotes. Even this is **not** entitlement to 661 days, no 21–45d lifecycle, no simultaneous fills, no historical fee/margin, no economic return. Empty gzip is BLOCK.
- A separate deterministic local test must exercise absent key, malformed gzip, future timestamp, missing asset, invalid bid/ask and a positive bounded gzip fixture. Fixtures are explicitly synthetic.
- GitHub workflow must publish only the compact redacted JSON summary, never licensed market data, and preserve research-only branch and all sealed/frozen records.

**Next after source proof:** written 2021-12-09..2023-09-30 full BTC+ETH licensed coverage, private archive storage and original full lifecycle, historical account-specific fee/delivery/margin/liquidation terms; then independent five-fold economic TRAIN. No ROI/promotion based on this source check.
