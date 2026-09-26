# V99 R106 Phase145 — Cross-Venue Range-Intensity Divergence Preregistration

Status: **PREREGISTERED / NO PHASE145 PNL OBSERVED**

Frozen while Phase144 is still running and before its result is known. This is a scientifically distinct OHLC hypothesis: it measures venue-specific realized intrahour range intensity rather than close location, volume, return spread, or volatility history.

## Scientific premise

For venue `v`, asset `i`, completed hour `t`, define a dimensionless completed-candle range intensity:

`RI[v,i,t] = (high[v,i,t] - low[v,i,t]) / open[v,i,t]`

An observation is admissible only when OHLC are finite, `open > 0`, and `high >= low`. No epsilon, clipping, imputation, forward/back fill, alternate price denominator, or symbol substitution is allowed. Before any PnL, every asset must have >=98% aligned valid TRAIN observations on both venues.

Define the cross-venue feature exactly as:

`divergence[i,t] = RI[OKX,i,t] - RI[Binance,i,t]`

Normalize each asset with exact same-window 168-hour median/MAD (`median(abs(window - median(window)))`), then cross-sectionally demean normalized scores. Freeze **reversion** direction: relatively greater OKX range intensity versus Binance receives lower next-hour relative weight. Shift the complete score exactly `t-1` before execution.

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
- no grid, sign flip, threshold rescue, clipping rescue, selective asset removal, symbol substitution, or post-hoc direction change
- holdout rows used for construction/selection: 0/0
- V16 Frozen and V99 Frozen immutable

## Gate sequence

1. semantic/alignment/coverage/hash integrity gate;
2. TRAIN alpha + four temporal folds;
3. only if TRAIN passes: severe and supersevere costs;
4. only if costs pass: tails, concentration, regime matrix, benchmark envelope, reproducibility;
5. untouched holdout only after formal freeze under the existing protocol.

Failure at any gate is permanent for this frozen formulation. No rescue or tuning.
