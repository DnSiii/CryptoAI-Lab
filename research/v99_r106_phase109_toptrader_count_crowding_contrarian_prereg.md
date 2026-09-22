# V99 R106 Phase109 — top-trader account-count crowding contrarian train-only preregistration

## Hypothesis
Before any Phase109 PnL is observed, test one distinct Binance USD-M positioning hypothesis: extreme cross-sectional long/short crowding among top-trader accounts is contrarian at the next tradable hour. This isolates the account-count top-trader cohort directly, rather than the position-weighted conviction tested in Phase107 or the size-vs-count divergence tested in Phase106.

## Frozen specification
- Source: official Binance USD-M daily metrics archives already admitted by Phase63; train dates only.
- Field: `count_toptrader_long_short_ratio`.
- Raw feature: `log(count_toptrader_long_short_ratio)`.
- At each hour: cross-sectional median/MAD robust z-score, requiring >=10 simultaneous assets and nonzero MAD.
- Direction: contrarian; high top-trader account-count long tilt is short and low tilt is long.
- Causality: transform contemporaneous cross-section, then shift the whole alpha by exactly one hour (`t-1`) before trading.
- Bounded signal: negative `tanh`; cross-sectional L1 normalization; fixed alpha gross 0.20.
- Costs: severe first gate using the existing canonical execution/cost machinery.
- Selection: chronological train only through the Phase63 train end; existing temporal folds and `stable_train` gate.
- Missing archives or historical files lacking the field are unavailable data and are not filled, inferred, or imputed.
- No parameter grid, sign flip, rescue, threshold search, retuning, or holdout parsing.

## Decision
PASS only if the existing `stable_train` diagnostic passes. PASS freezes this exact specification for supersevere, regime matrix, benchmark-envelope and reproducibility gates before any untouched-holdout access. FAIL is permanent for this specification.

V16 Frozen and V99 Frozen are immutable throughout.
