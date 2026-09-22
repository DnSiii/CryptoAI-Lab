# V99 R106 Phase118 — raw aggTrades availability/provenance audit preregistration

Phase118 is an **AVAILABILITY/PROVENANCE AUDIT ONLY**. It is preregistered while independent train-only candidates are still running and cannot affect their specifications or decisions.

## Motivation
The R106 line has already studied hourly OHLCV-derived trade count/size and taker-volume aggregates, but has no study using the official raw USD-M `aggTrades` archive. Raw aggregate trades preserve event-level price, quantity, timestamp and buyer-maker direction that are collapsed by hourly bars. Before any event-level microstructure hypothesis is allowed, establish whether the official archive has enough train history under the unchanged temporal-fold protocol.

## Frozen audit contract
- Canonical PIT48 symbols only.
- Official Binance public-data object listing under `data/futures/um/daily/aggTrades/<SYMBOL>/`.
- Admit only archive dates 2021-12-01 <= date < 2024-01-18. Boundary-day 2024-01-18 is excluded.
- Phase118 reads **object metadata only**: key, size, last-modified/listing metadata. It downloads/parses no trade archive content.
- Inventory per symbol: first/last admitted date, observed files, expected files within admitted span, explicit missing dates, coverage ratio and listed compressed bytes.
- Report coverage by the existing four temporal folds and whether source availability can plausibly satisfy the unchanged >=3-valid-fold gate.
- Do not infer missing files, use mirrors, or substitute APIs/third-party datasets.
- Do not compute price/quantity/buyer-maker values, returns, PnL, predictive correlations, directions, horizons, thresholds, regimes, benchmark comparisons or holdout market values.

## Decision
If archive coverage cannot support >=3 existing folds, close raw aggTrades for this R106 protocol without alpha testing. If it can, a separate integrity/ingestion phase is required before any alpha preregistration.

V16 Frozen and V99 Frozen remain immutable.
