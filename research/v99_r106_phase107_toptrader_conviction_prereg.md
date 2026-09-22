# V99 R106 Phase107 — top-trader conviction train-only preregistration

## Hypothesis
Before any Phase107 PnL is observed, test one simpler Binance USD-M futures positioning hypothesis that is distinct from Phase105/106 divergence constructions: the absolute position-weighted top-trader long/short tilt itself contains directional continuation information. A relatively larger position-weighted top-trader long/short ratio predicts relative upside; a relatively smaller ratio predicts relative downside.

## Frozen specification
- Source: official Binance USD-M daily metrics archives already admitted by Phase63; train dates only.
- Field: `sum_toptrader_long_short_ratio` only.
- Raw feature: `log(sum_toptrader_long_short_ratio)`.
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
