# V98 Independent Phase 026 — Residual Trend Efficiency

## Preregistration

Phase025 liquidity-efficiency is rejected on training and all downstream gates remain closed. This experiment does not tune Phase025 and does not use V99 or validation/holdout observations.

## Hypothesis

Cross-sectional assets whose lagged BTC-residual returns travel persistently in one direction with relatively little path noise may exhibit a structural trend-efficiency premium. The signal is signed residual displacement divided by residual path length over a fixed 30-day window. This differs from raw residual momentum by penalizing noisy/choppy paths rather than rewarding displacement alone.

## Fixed design before result inspection

- PIT liquid universe: top 10 by existing causal 30-day liquidity view; minimum 90-day history.
- BTC beta: fixed 30-day rolling estimate using only lagged hourly returns.
- Residual return: asset lagged hourly return minus rolling beta times BTC lagged hourly return.
- Signal window: 720 hours. `sum(residual) / sum(abs(residual))`; no sign inversion.
- Cross-sectional centered percentile score at each timestamp.
- Dollar and BTC-beta neutralization by cross-sectional projection.
- Rebalance every 48 hours.
- Gross target/cap 0.75; no leverage search.
- Existing base, severe and supersevere cost/funding model unchanged.
- Existing chronological folds and training gates unchanged.
- Validation is evaluated only if the training gate passes. Final holdout remains untouched in this phase even if validation passes; a passing candidate must first be frozen.

## Anti-overfit constraints

No parameter grid, neighborhood search, sign search, cadence search, regime filter, leverage adjustment, or post-result rescue is permitted. If rejected, close this exact trend-efficiency hypothesis and move to another independent family.
