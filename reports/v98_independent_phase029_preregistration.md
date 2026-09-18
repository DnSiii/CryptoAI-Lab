# V98 Independent — Phase 029 preregistration

## Hypothesis
Cross-sectional **residual trend efficiency** may contain alpha distinct from raw residual momentum, residual shock recovery, low-volatility, beta stability, tail shape, liquidity efficiency and calendar seasonality. Persistent idiosyncratic displacement that accumulates smoothly rather than through a single shock may be more likely to reflect durable asset-specific information; noisy displacement should be downweighted.

## Fixed specification before execution
- Universe: point-in-time top-10 liquid assets, 720h liquidity lookback, minimum 2160h history; BTC excluded from traded names.
- All signal inputs use close.shift(1); no contemporaneous/future bars.
- BTC beta: rolling 720h, minimum 360h.
- Residual return: hourly asset return minus rolling-beta × BTC hourly return.
- Trend horizon: fixed 168h cumulative residual return.
- Path-noise denominator: fixed 168h sum of absolute hourly residual returns; efficiency = residual 168h sum / residual absolute-path sum. No alternate horizon or transformation search.
- Score: cross-sectional percentile rank of efficiency minus 0.5; continuation sign fixed ex ante.
- Cross-sectional score is beta- and dollar-neutralized by OLS projection at each rebalance.
- Rebalance every 24h; gross target/cap 0.75. No leverage search.
- One specification only: no lookback, sign, cadence, threshold, regime, universe or leverage grid/search.

## Gates / evidence
Use the existing V98 Independent chronological training folds and training gate. Report base, severe and supersevere costs/funding; regimes; concentration/tails; worst day; max drawdown; Profit Factor; payoff; win rate; positive days; beta neutrality and reproducibility/invariant tests. Validation may be inspected only if the training gate passes. Final holdout remains untouched unless a candidate passes training and validation and is formally frozen.

## Decision rule
If rejected, close residual trend-efficiency without sign inversion, horizon rescue or blending with Phase017/019. If training passes, proceed directly to the existing validation gate. Only a materially robust validation pass may become the internal V98 champion pending one-shot final holdout.
