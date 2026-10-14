# V98 Independent Phase243 — Clean-4 source quarantine policy and acquisition preregistration

Status: PREREGISTERED BEFORE ANY INTEGRATED V98 SYSTEM PNL.

## Why this exists

The frozen XRPUSDT 2023-11-14 11:00 UTC source is not decision-grade: checksum-matched monthly 1h and daily 1h agree with each other but violate physical quote/base bounds; daily 1m disagrees; the independently preregistered same-provider aggTrades tape agrees with neither complete candle representation. The tape result is QUARANTINED_SOURCE_CONFLICT and computed no alpha/PnL.

Therefore XRP is quarantined for source integrity only. This is not performance-based asset deletion and must not be interpreted as evidence that removing XRP improves returns.

## Frozen Clean-4 universe

- BTCUSDT
- ETHUSDT
- BNBUSDT
- SOLUSDT

XRPUSDT is excluded from Phase243 integrated research until an independent provenance rule resolves the contradiction. Re-entry, if ever allowed, requires a separate preregistration before system PnL.

## Frozen source contract

- Binance USD-M monthly 1h klines from data.binance.vision.
- December 2022 warmup plus every month 2023-01 through 2025-12.
- Exact provider .CHECKSUM verification for every ZIP.
- Existing Phase243 parser and physical/source-integrity rules remain unchanged.
- Exact chronological coverage per asset: 27,048 hourly bars from 2022-12-01 00:00 UTC through 2025-12-31 23:00 UTC.
- Expected archives: 4 assets × 37 months = 148.
- Expected asset-hours: 108,192.
- No 2026+ download, read, hash, summary, validation or holdout access.
- Existing native V98 Phase206 funding CSVs are validated on the same Clean-4 universe with the existing 8h PIT source gate.

## PASS gate

PASS_CLEAN4_SOURCE_DATA_ONLY_NO_ALPHA requires:
1. all 148 archives downloaded or cache-reused from the frozen source;
2. every archive matches its provider SHA256 sidecar;
3. every archive passes the existing exact schema/calendar/OHLC/base-quote/taker-side/residual checks;
4. each canonical asset panel has exactly 27,048 continuous hourly rows;
5. no two asset canonical price/volume panels are byte-fingerprint identical;
6. all four native funding series pass the existing Phase243 source gate;
7. canonical outputs and manifest hashes are persisted;
8. holdout_accessed=false, alpha_or_pnl_computed=false, V16/V99 unused.

Any failure remains DATA_ONLY and cannot be used to alter a strategy.

## Consequence

A PASS only unlocks construction/evaluation of the first complete V98 engine on the Clean-4 authenticated training universe. It does not promote a strategy or open validation/holdout.
