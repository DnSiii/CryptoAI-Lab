# V98 Independent — Phase 036 Wick-Imbalance Pressure — Preregistration

Status: preregistered after Phase035 rejection; no Phase036 result has been observed.

## Hypothesis
Persistent asymmetry between upper and lower candle wicks may capture repeated rejection pressure inside the auction that is not identical to close-location (Phase035), close-to-close residual trend, volatility, liquidity, funding, beta structure, seasonality, or lead-lag. A candle with a relatively longer lower wick than upper wick records stronger rejection of lower prices; persistent cross-sectional differences may predict subsequent returns.

## Frozen specification
- Point-in-time top-10 liquid universe; BTC excluded from tradable targets.
- Liquidity lookback 720h; minimum history 2160h.
- Every OHLC input shifted one full bar before feature construction.
- Per-bar upper wick = high - max(open, close); lower wick = min(open, close) - low.
- Wick-imbalance = (lower_wick - upper_wick)/(high-low), zero when range is numerically zero.
- Signal: simple 24h mean of lagged wick-imbalance, minimum 18 observations.
- Rebalance every 24h.
- Cross-sectional rank transform, then neutralize against intercept and lagged 720h unconditional BTC beta.
- Gross target/cap 0.75.
- No sign inversion, lookback/cadence/gross/threshold/regime search after results.

## Evaluation
Existing chronological training folds and unchanged V98 gates. Base realistic costs/funding and severe/supersevere stresses; regime, concentration/tails, max drawdown, PF, payoff, win rate, positive days, reproducibility and beta-neutrality diagnostics. Validation only after a training pass. Final holdout untouched unless formally frozen after training+validation.

## Anti-overfit decision
If rejected, close the wick-imbalance family without rescue tuning and proceed to another orthogonal source. Phase035 results are not used to choose sign or parameters; Phase036 uses the conventional interpretation that longer lower wicks indicate rejection of lower prices.