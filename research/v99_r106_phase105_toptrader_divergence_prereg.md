# V99 R106 Phase105 — top-trader divergence train-only preregistration

## Hypothesis
Before any Phase105 PnL is observed, test one orthogonal Binance USD-M futures positioning hypothesis: cross-sectional divergence between top-trader account long/short ratio and the global account long/short ratio contains directional information. A relatively more-long top-trader cohort versus the broad account population predicts relative continuation; relatively more-short predicts relative downside.

## Frozen specification
- Source: official Binance USD-M daily metrics archives already admitted by Phase63; train dates only.
- Fields: `count_toptrader_long_short_ratio` and `count_long_short_ratio`.
- Raw feature: `log(count_toptrader_long_short_ratio) - log(count_long_short_ratio)`.
- At each hour: cross-sectional median/MAD robust z-score, requiring >=10 simultaneous assets and nonzero MAD.
- Causality: shift the whole standardized alpha by exactly one hour (`t-1`) before trading.
- Bounded signal: `tanh`; cross-sectional L1 normalization; fixed alpha gross 0.20.
- Costs: severe first gate using the existing canonical execution/cost machinery.
- Selection: chronological train only through the Phase63 train end; existing temporal folds and `stable_train` gate.
- Missing archives are not filled or inferred.
- No parameter grid, sign flip, rescue, threshold search, retuning, or holdout parsing.

## Decision
PASS only if the existing `stable_train` diagnostic passes. PASS freezes this exact specification for supersevere, regime matrix, benchmark-envelope and reproducibility gates before any untouched-holdout access. FAIL is permanent for this specification.

V16 Frozen and V99 Frozen are immutable throughout.
