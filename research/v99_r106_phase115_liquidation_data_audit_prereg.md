# V99 R106 Phase115 — liquidationSnapshot availability/integrity audit preregistration

Phase115 is a **DATA AVAILABILITY / INTEGRITY AUDIT ONLY**. It is preregistered after the Phase114 temporal-admissibility decision and before any liquidation-based PnL.

## Motivation
Forced-liquidation events are structurally orthogonal to OHLCV, funding, premium, open interest, long/short positioning, taker flow and aggregate bookDepth. The Binance USD-M public archive historically exposed a daily `liquidationSnapshot` family, but current availability must be measured rather than assumed.

## Frozen audit contract
- Canonical PIT48 symbols only.
- Relevant selection window: 2021-12-01 00:00 UTC through train end 2024-01-18 00:00 UTC.
- Query only official Binance public-data object metadata under `data/futures/um/daily/liquidationSnapshot/<SYMBOL>/`.
- Admit archive dates strictly before 2024-01-18, so a boundary-day file that could contain post-train observations is never downloaded.
- If admitted files exist, inventory per-symbol first/last date, file count, missing dates and coverage; verify a deterministic first-available file per calendar quarter using SHA256 + ZIP CRC.
- If CSVs are available, inventory schema and validate parseable event timestamps and finite nonnegative quantity/price-like numeric fields where present. Explicitly detect duplicate rows/events rather than silently deduplicating.
- If the official historical archive is no longer available, record that as `DATA_SOURCE_UNAVAILABLE`; do not substitute scraped mirrors, third-party datasets, APIs with different coverage, or reconstructed events.
- No relation to returns/PnL/regimes/benchmarks; no direction/horizon/threshold; no holdout market values.

## Decision
Only a sufficiently available pre-train source that can support the existing >=3-valid-fold requirement may justify a later separately preregistered liquidation alpha. Otherwise the family is closed for this R106 protocol without weakening gates.

V16 Frozen and V99 Frozen remain immutable.
