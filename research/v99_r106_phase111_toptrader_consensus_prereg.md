# V99 R106 Phase111 — top-trader position-and-account consensus train-only preregistration

## Hypothesis
Before any Phase111 PnL is observed, test the complementary, scientifically distinct state to rejected Phase110: cross-sectional agreement between position-weighted top-trader long/short conviction and top-trader account-count long/short positioning predicts next-hour relative returns. Phase110 isolated opposite-sign disagreement and failed. Phase111 does not invert or retune Phase110; it tests the separately preregistered economic mechanism that agreement across the two independently standardized top-trader cohorts represents stronger informed positioning.

## Frozen specification
- Source: official Binance USD-M daily metrics archives admitted by Phase63; train dates only through 2024-01-18.
- Fields: `sum_toptrader_long_short_ratio` and `count_toptrader_long_short_ratio`.
- Raw features: log of each positive ratio.
- At each hour independently compute cross-sectional median/MAD robust z-scores for both fields, requiring >=10 simultaneous assets and nonzero MAD.
- Consensus mask: retain only assets where both robust z-scores have the same nonzero sign (`z_sum * z_count > 0`).
- Direction/magnitude: consensus score `(z_sum + z_count) / 2` on the consensus mask; zero otherwise. This direction is fixed before PnL and is not chosen from Phase110 results.
- Causality: shift the complete contemporaneous alpha exactly one hour (`t-1`) before trading.
- Bounded signal: `tanh`; cross-sectional L1 normalization; fixed alpha gross 0.20.
- Costs: severe first gate using canonical execution/cost machinery.
- Selection: chronological train only; existing temporal folds and `stable_train` gate.
- Missing archives/fields remain unavailable; no fill, inference, or imputation.
- No parameter grid, threshold search, sign flip, rescue, retuning, or holdout parsing.

## Decision
PASS only if existing `stable_train` passes. PASS freezes this exact specification for supersevere, regime matrix, benchmark-envelope and reproducibility gates before untouched holdout. FAIL is permanent for this specification.

V16 Frozen and V99 Frozen are immutable throughout.
