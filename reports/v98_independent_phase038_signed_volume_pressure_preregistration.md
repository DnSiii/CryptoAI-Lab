# V98 Independent — Phase 038 Signed Volume Pressure — Preregistration

Status: preregistered after Phase037 training rejection; no Phase038 result has been observed.

## Hypothesis
Directional participation may matter more than unsigned attention: persistent lagged quote-volume occurring with positive versus negative returns can proxy net aggressive flow/accumulation pressure. This differs from Phase011's unsigned volume expansion and from pure price momentum because return direction is weighted by relative traded notional before cross-sectional ranking.

## Frozen specification
- Point-in-time top-10 liquid universe; BTC excluded from tradable targets; 720h liquidity lookback and 2160h minimum history.
- All return and quote-volume inputs shifted one full bar before feature construction.
- Relative quote volume = lagged quote volume / its 720h rolling median (minimum 360 observations), clipped to [0, 5] only for numerical/outlier robustness.
- Signed flow observation = sign(lagged hourly return) * relative quote volume.
- Signal = simple 24h mean signed flow, minimum 18 observations.
- Rebalance every 24h; conventional sign only (long higher signed pressure, short lower).
- Rank cross-sectionally and neutralize intercept plus lagged 720h BTC beta (minimum 360 observations).
- Gross target/cap 0.75.
- No sign/window/cadence/gross/clipping/regime/threshold search after results.

## Evaluation
Existing chronological training folds and unchanged V98 gates. Base realistic costs/funding plus severe/supersevere stresses; regimes, concentration/tails, max drawdown, PF, payoff, win rate, positive days, reproducibility and beta-neutrality diagnostics. Validation only after training pass; final holdout remains untouched until a formally frozen candidate clears training+validation.

## Anti-overfit decision
If rejected, close signed-volume pressure without rescue tuning or sign inversion. V99 is not consulted for design or selection.