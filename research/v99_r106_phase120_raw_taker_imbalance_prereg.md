# V99 R106 Phase120 — raw aggTrades taker-imbalance train-alpha preregistration

Phase120 is the first alpha hypothesis authorized after Phase118 availability and Phase119 integrity/resource gates. It is frozen before any raw `aggTrades` return relation is computed.

## Scientific hypothesis
Event-level aggressive-flow imbalance contains information discarded by hourly OHLCV taker-volume aggregates. For each admitted symbol/hour, compute signed raw quantity from official USD-M aggregate trades: `+qty` when `is_buyer_maker=false` (aggressive buy) and `-qty` when `is_buyer_maker=true` (aggressive sell). Define hourly imbalance `(taker_buy_qty - taker_sell_qty)/(taker_buy_qty + taker_sell_qty)`. Cross-sectionally robust-standardize the imbalance by contemporaneous median/MAD, apply `tanh`, L1-normalize, and shift the **entire alpha by one hour (t-1)** before execution. Direction is continuation; no sign flip is permitted.

## Frozen resource-safe universe rule
Full raw PIT48 is ~95.36 GB compressed. Before any alpha values are read, choose exactly the **12 PIT48 symbols with the smallest Phase118 listed pre-holdout compressed byte totals**, ties lexicographically. This is a deterministic source-resource criterion fixed from metadata only, not returns, PnL, direction, or predictive performance. No symbol may be substituted after results are seen. Require >=8 simultaneously valid selected symbols per hour.

## Frozen protocol
- Source: official Binance USD-M `daily/aggTrades` archives + matching CHECKSUM only.
- Dates: 2021-12-01 through 2024-01-17 inclusive; 2024-01-18 and later prohibited.
- Exact Phase118 missing-date inventory governs downloads; no interpolation/mirror/API substitution.
- Verify SHA256 and ZIP CRC on every archive consumed.
- Aggregate raw event quantity to UTC 1h buckets; no price-derived feature is allowed.
- Alpha gross: 0.20.
- Existing causal execution/cost engine unchanged.
- Severe cost is the train gate cost.
- Existing four chronological temporal folds and unchanged `stable_train` gate apply.
- Selection is train-only; holdout market values remain unparsed.
- No parameter grid, threshold search, horizon search, sign search, symbol-count search, or post-result retuning.

## Decision ladder
FAIL at train/fold gate => permanent rejection with no retuning. PASS => freeze this exact specification and proceed, in order, to supersevere cost, regime matrix, benchmark envelope and reproducibility gates before untouched holdout can be considered. A downstream failure rejects the candidate.

V16 Frozen and V99 Frozen remain immutable.