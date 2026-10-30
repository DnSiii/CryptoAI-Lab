# V98 Independent — Phase 035 Close-Location Pressure — Conditional Preregistration

Status: preregistered while Phase034 is unresolved; execute only if Phase034 is rejected. No Phase035 result has been observed.

## Hypothesis
Persistent closing location within each candle's high-low range may measure directional auction pressure that is distinct from close-to-close residual trend, volume attention, liquidity efficiency and lead-lag effects. Cross-sectional differences in lagged close-location pressure may therefore predict subsequent returns.

## Frozen specification
- Point-in-time top-10 liquid universe; BTC excluded from tradable targets.
- Liquidity lookback 720h; minimum history 2160h.
- Every OHLC input shifted one full bar before feature construction.
- Per-bar close-location value: CLV = (2*close - high - low)/(high-low), zero when range is numerically zero.
- Signal: simple 24h mean of lagged CLV, minimum 18 observations.
- Rebalance every 24h.
- Cross-sectional rank transform, then neutralize against intercept and lagged 720h unconditional BTC beta.
- Gross target/cap 0.75.
- No sign inversion, lookback/cadence/gross/threshold/regime search after results.

## Evaluation
Existing chronological training folds and unchanged V98 gates. Base realistic costs/funding and severe/supersevere stresses; regime, concentration/tails, max drawdown, PF, payoff, win rate, positive days, reproducibility and beta-neutrality diagnostics. Validation only after a training pass. Final holdout untouched unless formally frozen after training+validation.

## Anti-overfit decision
If rejected, close the close-location-pressure family without rescue tuning and proceed to another orthogonal source.