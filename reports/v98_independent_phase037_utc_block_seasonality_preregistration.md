# V98 Independent — Phase 037 UTC 8h Block Residual Seasonality — Preregistration

Status: preregistered after Phase036 rejection; no Phase037 result has been observed.

## Hypothesis
Crypto perpetual markets have globally synchronized 8-hour settlement/funding clocks and recurring regional liquidity handoffs. The cross-sectional residual return associated with the same UTC 8-hour block may therefore contain a persistent, causal flow-seasonality component distinct from weekday seasonality (Phase027), funding carry level (Phase009), price trend/reversal, liquidity, beta structure, OHLC auction-shape, and lead-lag families.

## Frozen specification
- Point-in-time top-10 liquid universe; BTC excluded from tradable targets.
- Liquidity lookback 720h; minimum history 2160h.
- Close-to-close returns are shifted one full bar before signal use.
- Estimate lagged 720h unconditional BTC beta with minimum 360 observations; form beta-residual hourly returns.
- Aggregate residual returns into non-overlapping UTC blocks [00:00,08:00), [08:00,16:00), [16:00,24:00).
- At each 8h boundary, estimate each asset's expected residual return for the upcoming block using only the prior 30 observations of that same UTC block, minimum 20 observations.
- Conventional sign only: long assets with higher historical same-block residual return and short lower-ranked assets.
- Rebalance every 8h at UTC 00/08/16 boundaries.
- Cross-sectional rank transform, then neutralize against intercept and lagged unconditional BTC beta.
- Gross target/cap 0.75.
- No block selection, sign inversion, lookback/minimum-history/cadence/gross/threshold/regime search after results.

## Evaluation
Existing chronological training folds and unchanged V98 gates. Base realistic costs/funding and severe/supersevere stresses; regime, concentration/tails, max drawdown, PF, payoff, win rate, positive days, reproducibility and beta-neutrality diagnostics. Validation only after a training pass. Final holdout untouched unless formally frozen after training+validation.

## Anti-overfit decision
If rejected, close the UTC-block seasonality family without rescue tuning. The three blocks are used symmetrically; no favorable block may be selected after observing results. V99 is not consulted for signal design or selection.