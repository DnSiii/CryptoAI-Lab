# V99 R106 Phase143 — Cross-Venue Volume-Shock Asymmetry Preregistration

Status: **PREREGISTERED / BLOCKED UNTIL PHASE140–142 DECISIONS**

Frozen before observing any Phase140 alpha PnL. This hypothesis is distinct from raw participation (Phase140), turnover intensity (Phase141), and volume-price absorption (Phase142): it tests whether disagreement in standardized venue-specific volume shocks carries next-hour cross-sectional information.

## Data prerequisite

Use only the direct semantically comparable hourly USDT quote-notional fields admitted by the Phase140 data gate for BTC, ETH, SOL, XRP, DOGE. No proxy substitution, symbol substitution, forward/back fill, epsilon/log1p repair, or selective asset removal.

## Frozen feature

For each venue and asset, require strictly positive notional volume and compute `lv_t = log(notional_volume_t)`. Define each venue shock as `lv_t - median_168h(lv)` using exactly 168 completed hours. Scale each venue shock by its own exact same-window MAD `median(abs(window - median(window)))`. Define `shock_asymmetry_t = zshock_OKX_t - zshock_Binance_t`, cross-sectionally demean across the five assets each hour, freeze **reversion** direction, normalize portfolio gross/L1 <= 1, then shift the complete score exactly t-1 before execution.

## Frozen contracts

- chronological TRAIN only; holdout rows for construction/selection 0/0
- exact 168 completed-hour median/MAD; no alternate windows
- strictly positive finite direct quote-notional volumes; otherwise DATA_INADMISSIBLE
- four chronological temporal folds
- no sign flip, grid, threshold rescue, parameter search, symbol substitution, selective asset removal, or post-result redesign
- V16 Frozen and V99 Frozen immutable

## Gate sequence

Phase140–142 decisions -> TRAIN alpha/folds -> severe/supersevere -> tails/concentration/regime matrix -> benchmark envelope/reproducibility -> formal freeze -> untouched holdout.

Failure at TRAIN is permanent for this exact hypothesis.