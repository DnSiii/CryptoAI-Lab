# V99 R106 Phase148 — Cross-Venue Body/Range Ratio Divergence Preregistration

Status: **PREREGISTERED / NO PHASE148 PNL OBSERVED AT PREREGISTRATION**

Frozen after Phase147 rejection and before any Phase148 PnL is observed. This is scientifically distinct from Phase144 close-location, Phase145 full-range intensity, Phase146 signed body intensity, and Phase147 wick imbalance: it measures venue disagreement in the fraction of each completed candle's range occupied by the signed body.

## Scientific premise

For venue `v`, asset `i`, completed hour `t`, define exactly:

`range[v,i,t] = high[v,i,t] - low[v,i,t]`

`BR[v,i,t] = (close[v,i,t] - open[v,i,t]) / range[v,i,t]`

Admissible observations require finite OHLC, `open > 0`, `high >= max(open,close)`, `low <= min(open,close)`, and `range > 0`. Zero-range candles are missing observations, not repaired. No epsilon, clipping, imputation, forward/back fill, alternate denominator, symbol substitution, selective asset removal, or candle repair. Every asset must have >=98% aligned valid TRAIN observations on both venues before PnL.

Define exactly:

`divergence[i,t] = BR[OKX,i,t] - BR[Binance,i,t]`

Normalize per asset with exact same-window 168-hour median/MAD (`median(abs(window - median(window)))`), cross-sectionally demean, and freeze **reversion** direction. Shift the complete score exactly `t-1` before execution.

## Frozen contracts

- universe: BTC, ETH, SOL, XRP, DOGE mappings audited in Phase136
- direct completed 1h OHLC only; no proxy source
- TRAIN only for feature construction and selection
- aligned-valid coverage >=98% per asset before PnL
- exact 168h same-window median/MAD
- cross-sectional demeaning: yes
- direction: reversion
- complete-score execution shift: exactly t-1
- gross/L1 <= 1
- four chronological temporal folds
- no grid, sign flip, threshold rescue, clipping rescue, selective asset removal, symbol substitution, candle repair, or post-hoc direction change
- holdout rows used for construction/selection: 0/0
- V16 Frozen and V99 Frozen immutable

## Gate sequence

1. semantic/alignment/coverage/hash integrity gate;
2. TRAIN alpha + four temporal folds;
3. only if TRAIN passes: severe and supersevere costs;
4. only if costs pass: tails, concentration, regime matrix, benchmark envelope, reproducibility;
5. untouched holdout only after formal freeze under the existing protocol.

Failure at any gate is permanent for this frozen formulation. No rescue or tuning.
