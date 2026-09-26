# V99 R106 Phase140 — Cross-Venue Volume-Participation Data/Hypothesis Preregistration

Status: **PREREGISTERED / NOT YET EXECUTED**

Frozen before observing Phase139 PnL and before any Phase140 PnL. This is orthogonal to Phase137 price dislocation, Phase138 return innovation, and Phase139 realized-volatility dispersion.

## Scientific premise

Temporary migration of trading participation between OKX and Binance may contain information not present in price/return direction. First audit whether causally aligned hourly quote-volume (or a directly comparable notional-volume field) exists for both venues across the same five Phase136 instruments and TRAIN window. No PnL may be computed unless the fields are semantically comparable and meet the coverage/integrity gate.

If and only if the data gate passes, freeze the feature without parameter search:

`participation_t = log(OKX_notional_volume_t) - log(Binance_notional_volume_t)`

Normalize each asset with exact same-window median/MAD over 168 completed hours, cross-sectionally demean each hour, and use **reversion** as the frozen economic direction: unusually OKX-heavy relative participation receives lower next-hour relative weight and unusually Binance-heavy participation receives higher weight. Shift the complete score by exactly `t-1` before execution.

## Frozen contracts

- universe: BTC, ETH, SOL, XRP, DOGE mappings already audited in Phase136
- frequency: 1h; chronological TRAIN only
- data gate first: semantic comparability + >=98% valid aligned TRAIN coverage per asset + no forward/back fill + duplicate/gap audit
- normalization: exact same-window 168h median/MAD, `median(abs(window - median(window)))`
- cross-sectional demeaning: yes
- direction: reversion
- complete score execution shift: exactly t-1
- gross/L1 <= 1
- four chronological temporal folds
- no grid, sign flip, symbol substitution, threshold rescue, or selective asset removal
- holdout rows for feature construction/selection: 0/0
- V16 Frozen and V99 Frozen immutable

## Gate sequence

1. independent source/semantic/coverage/integrity audit only;
2. if data passes, TRAIN alpha + temporal folds;
3. only if TRAIN passes, severe and supersevere costs;
4. only if those pass, tails/concentration/regime matrix, benchmark envelope and reproducibility;
5. untouched holdout only after formal candidate freeze under the existing protocol.

If the data fields are not semantically comparable, reject Phase140 as DATA_INADMISSIBLE without proxy substitution. If TRAIN fails, reject permanently without sign flip or tuning.
