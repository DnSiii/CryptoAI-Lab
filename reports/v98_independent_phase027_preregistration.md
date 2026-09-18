# V98 Independent Phase 027 — Causal Weekday Residual Seasonality

## Prior evidence diagnosis

Phase026 produced positive aggregate training return but failed robustness: PF 1.090, worst day -19.12%, 2023 return -10.26% / PF 0.898, severe PF 1.034, supersevere PF 0.954 and supersevere DD -61.19%. Its edge was concentrated in 2024/bull conditions, so the residual trend-efficiency family is closed without window/sign/cadence rescue.

## Hypothesis

Crypto's continuous market can exhibit recurring weekday-specific flows. An asset's own lagged BTC-residual daily return history for the same UTC weekday may contain a low-turnover seasonal cross-sectional signal distinct from momentum, volatility, liquidity, funding carry, and residual path-shape signals already tested.

## Fixed design

- Existing PIT top-10 liquid universe and 90-day minimum history.
- Fixed 30-day causal BTC beta using lagged hourly returns.
- Construct lagged 24-hour residual returns.
- At each 00:00 UTC daily rebalance, estimate each eligible asset's expected residual return from the last 26 observations of the same UTC weekday only; require at least 13 observations.
- Cross-sectional centered percentile score; no sign inversion.
- Dollar/BTC-beta neutral projection.
- Rebalance every 24 hours at 00:00 UTC; gross target/cap 0.75.
- Existing base/severe/supersevere transaction-cost and funding assumptions unchanged.
- Existing training folds/gates unchanged; validation only after training pass; final holdout remains untouched.

## Anti-overfit

Exactly one seasonal specification is tested. No weekday selection, weekday exclusion, lookback grid, sign search, cadence search, regime filter, leverage search, or post-result rescue. If rejected, close this weekday-seasonality family.
