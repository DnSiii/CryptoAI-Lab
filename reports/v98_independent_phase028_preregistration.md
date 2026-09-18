# V98 Independent — Phase 028 preregistration

## Hypothesis
Cross-sectional residual **shock recovery** may contain alpha distinct from persistent residual momentum, low-vol, beta stability, tail shape, liquidity efficiency and calendar seasonality. Assets suffering an unusually negative idiosyncratic daily shock relative to their own lagged residual volatility may subsequently mean-revert as forced/deleveraging flow normalizes; unusually positive shocks are symmetrically shorted.

## Fixed specification before execution
- Universe: point-in-time top-10 liquid assets, 720h liquidity lookback, minimum 2160h history; BTC excluded from traded names.
- All signal inputs use close.shift(1); no contemporaneous/future bars.
- BTC beta: rolling 720h, minimum 360h.
- Residual shock: sum of the most recent 24 lagged hourly BTC-residual returns.
- Scale: lagged 720h residual standard deviation, minimum 360h, multiplied by sqrt(24); score = negative shock / scale (contrarian sign fixed ex ante).
- Cross-sectional score is beta- and dollar-neutralized by OLS projection at each rebalance.
- Rebalance every 24h; gross target/cap 0.75. No leverage search.
- One specification only: no lookback, sign, cadence, threshold, regime, universe or leverage grid/search.

## Gates / evidence
Use the existing V98 Independent chronological training folds and training gate. Report base, severe and supersevere costs/funding; regimes; concentration/tails; worst day; max drawdown; Profit Factor; payoff; win rate; positive days; beta neutrality and reproducibility/invariant tests. Validation may be inspected only if the training gate passes. Final holdout remains untouched unless a candidate passes training and validation and is formally frozen.

## Decision rule
If rejected, close residual shock-recovery without sign inversion or parameter rescue. If training passes, proceed directly to the existing validation gate. Only a materially robust validation pass may become the internal V98 champion pending one-shot final holdout.