# V99 R106 Phase141 — Cross-Venue Turnover-Intensity Preregistration

Status: **PREREGISTERED / BLOCKED UNTIL PHASE140 DECISION**

Frozen before observing any Phase140 data-gate result or PnL. Phase141 is scientifically distinct from raw participation: it asks whether venue-specific notional turnover relative to its own trailing baseline carries information, rather than whether one venue simply has more absolute participation than the other.

## Data prerequisite

Use Phase140 direct, semantically comparable hourly USDT quote-notional fields only if its DATA gate passes for all five instruments. No proxy substitution, symbol substitution, forward/back fill, or selective asset removal. If Phase140 data are inadmissible, Phase141 is automatically DATA_INADMISSIBLE.

Because the frozen feature uses a logarithm, **every consumed notional-volume observation must be strictly positive**. A zero/negative/non-finite observation makes Phase141 DATA_INADMISSIBLE; do not add an epsilon, use `log1p`, impute, drop the hour/asset, or otherwise rescue the feature. This zero policy is frozen before any successful Phase140 data-gate result or Phase141 PnL is observed.

## Frozen feature

For each venue and asset, define `turnover_intensity_t = log(notional_volume_t) - median_168h(log(notional_volume))`, using only completed hours. Define cross-venue innovation as `OKX_turnover_intensity_t - Binance_turnover_intensity_t`. Scale each asset by exact same-window MAD over 168 completed hours, cross-sectionally demean each hour, and freeze **reversion** direction. Shift the complete score exactly t-1 before execution.

## Frozen contracts

- universe: BTC, ETH, SOL, XRP, DOGE mappings already audited in Phase136
- frequency: 1h; chronological TRAIN only
- trailing baseline and MAD: exactly 168 completed hours; no alternative windows
- exact MAD: `median(abs(window - median(window)))`
- direction: reversion; no sign flip
- cross-sectional demeaning: yes
- execution shift: exactly t-1
- gross/L1 <= 1
- four chronological temporal folds
- no grid, threshold rescue, symbol substitution, selective asset removal, or post-result feature redesign
- holdout rows for construction/selection: 0/0
- V16 Frozen and V99 Frozen immutable

## Gate sequence

Phase140 data admissibility -> TRAIN alpha/folds -> severe/supersevere -> tails/concentration/regime matrix -> benchmark envelope/reproducibility -> formal freeze -> untouched holdout.

Failure at TRAIN is permanent for this exact hypothesis; no sign flip or tuning is permitted.
