# V98 Independent — Phase 030 preregistration

## Hypothesis
Cross-sectional **funding carry** is a structurally different alpha source from all price-residual families tested so far. Persistently positive perpetual funding represents a direct transfer from longs to shorts, while persistently negative funding transfers from shorts to longs. A market-neutral portfolio long the most negative lagged funding and short the most positive lagged funding may harvest this transfer after realistic trading costs and stressed funding assumptions.

## Fixed specification before execution
- Universe: point-in-time top-10 liquid assets, 720h liquidity lookback, minimum 2160h history; BTC excluded from traded names.
- Funding inputs are shifted by one hour before feature construction; no contemporaneous/future funding observation is used.
- Signal: fixed 72h rolling mean of lagged funding rate, minimum 24 observed hourly slots; carry score = negative cross-sectional percentile rank of the rolling mean, centered at zero (negative-funding names long, positive-funding names short).
- BTC beta used only for portfolio neutralization: rolling 720h from close.shift(1) hourly returns, minimum 360h.
- Cross-sectional carry score is beta- and dollar-neutralized by OLS projection at each rebalance.
- Rebalance every 24h; gross target/cap 0.75. No leverage search.
- One specification only: no funding horizon, sign, cadence, threshold, regime, universe or leverage grid/search.

## Gates / evidence
Use the existing V98 Independent chronological training folds and training gate. Report base, severe and supersevere costs/funding, including the existing adverse funding debit/credit multipliers; regimes; concentration/tails; worst day; max drawdown; Profit Factor; payoff; win rate; positive days; beta neutrality and reproducibility/invariant tests. Validation may be inspected only if the training gate passes. Final holdout remains untouched unless a candidate passes training and validation and is formally frozen.

## Decision rule
If rejected, close funding carry without sign inversion, funding-window rescue, thresholding or price-signal blending. If training passes, proceed directly to the existing validation gate. Only a materially robust validation pass may become the internal V98 champion pending one-shot final holdout.
