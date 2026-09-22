# V99 R106 Phase106 — top-trader size divergence train-only preregistration

## Hypothesis
Before any Phase106 PnL is observed, test one distinct Binance USD-M futures positioning hypothesis: divergence between the position-weighted top-trader long/short ratio and the account-count top-trader long/short ratio contains directional information. When the position-weighted cohort is relatively more long than the count-based cohort, larger top-trader positions are tilted long and predict relative continuation; the converse predicts relative downside.

## Frozen specification
- Source: official Binance USD-M daily metrics archives already admitted by Phase63; train dates only.
- Fields: `sum_toptrader_long_short_ratio` and `count_toptrader_long_short_ratio`.
- Raw feature: `log(sum_toptrader_long_short_ratio) - log(count_toptrader_long_short_ratio)`.
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
