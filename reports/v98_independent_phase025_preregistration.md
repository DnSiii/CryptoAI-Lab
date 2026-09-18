# V98 Independent — Phase 025 preregistration

Status: **fallback only; do not execute unless Phase024 is rejected.**

## Prior evidence boundary
Phase023 beta-stability was rejected across training and every chronological fold. Phase024 residual-tail-shape is currently the active experiment. Phase025 is specified now, before Phase024 results are known, to prevent outcome-driven redesign.

## Hypothesis
Cross-sectional **liquidity efficiency** may contain an independent quality premium: among the point-in-time liquid universe, assets requiring less absolute price movement per unit of lagged dollar volume may be structurally less fragile and may outperform high-impact assets after dollar and BTC-beta neutralization.

## Fixed architecture
- Universe: same point-in-time liquid top-10 process used by recent V98 independent phases.
- Information lag: all signal inputs t-1 or earlier.
- BTC beta: trailing 720 hours, causal.
- Price-impact window: trailing 720 hours, causal.
- Per-hour impact primitive: `abs(return) / max(lagged_dollar_volume, epsilon)`; aggregate by rolling median to reduce domination by isolated prints.
- Signal: cross-sectional percentile rank of **negative** rolling impact, centered at zero.
- Portfolio: dollar-neutral and BTC-beta-neutral projection.
- Rebalance: 48 hours.
- Gross target/cap: 0.75 / 0.75; no leverage escalation.
- No parameter grid, sign flip, validation tuning, or V99 comparison.

## Gates
Use the existing V98 training gate unchanged: chronological folds, realistic base costs/funding, severe and supersevere stress, concentration/tails, worst day, max drawdown, PF, payoff, win rate and positive days. Validation may be opened only if the training gate passes. Final holdout remains untouched until a candidate is frozen after training + validation.

## Decision rule
If Phase025 fails, reject the liquidity-efficiency family without changing the 30d window, sign, rebalance cadence, or gross exposure in response to its results. Move to a genuinely different hypothesis family.
