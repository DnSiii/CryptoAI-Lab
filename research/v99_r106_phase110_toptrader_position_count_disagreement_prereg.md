# V99 R106 Phase110 — top-trader position-vs-account disagreement train-only preregistration

## Hypothesis
Before any Phase110 PnL is observed, test one distinct Binance USD-M positioning hypothesis: cross-sectional disagreement between position-weighted top-trader long/short conviction and top-trader account-count long/short crowding predicts next-hour relative returns. Unlike Phase106, which tested the raw size-vs-count divergence directly, Phase110 tests the *signed disagreement state*: only assets where the two standardized cohorts point in opposite directions carry alpha, with the position-weighted cohort treated as informed conviction and the account-count cohort as crowding.

## Frozen specification
- Source: official Binance USD-M daily metrics archives already admitted by Phase63; train dates only.
- Fields: `sum_toptrader_long_short_ratio` and `count_toptrader_long_short_ratio`.
- Raw features: log of each positive ratio.
- At each hour, independently compute cross-sectional median/MAD robust z-scores for position-weighted and account-count ratios, each requiring >=10 simultaneous assets and nonzero MAD.
- Disagreement mask: retain only assets where the two robust z-scores have opposite signs (`z_sum * z_count < 0`).
- Direction/magnitude: informed-minus-crowd score `z_sum - z_count` on the disagreement mask; zero otherwise.
- Causality: construct the contemporaneous cross-section and disagreement score, then shift the whole alpha by exactly one hour (`t-1`) before trading.
- Bounded signal: `tanh`; cross-sectional L1 normalization; fixed alpha gross 0.20.
- Costs: severe first gate using existing canonical execution/cost machinery.
- Selection: chronological train only through Phase63 train end; existing temporal folds and `stable_train` gate.
- Missing archives or historical files lacking either field are unavailable and are not filled, inferred, or imputed.
- No parameter grid, threshold search, sign flip, rescue, retuning, or holdout parsing.

## Decision
PASS only if the existing `stable_train` diagnostic passes. PASS freezes this exact specification for supersevere, regime matrix, benchmark-envelope and reproducibility gates before any untouched-holdout access. FAIL is permanent for this specification.

V16 Frozen and V99 Frozen are immutable throughout.
