# V99 R106 Phase67 — top-trader account/position disagreement preregistration

## Decision context
Phase66 is rejected on train-only evidence (0/4 healthy temporal folds; robust mean excluding top 1% negative). No holdout was inspected. Phase67 is a new single hypothesis, not a rescue or retune of Phase66.

## Hypothesis
Within Binance USD-M native metrics, divergence between top-trader position-weighted long/short ratio and top-trader account-count long/short ratio may identify cross-sectional conviction: large top-trader positions leaning more long than the top-trader account population imply positive relative conviction, and the inverse implies negative relative conviction.

## Frozen specification before execution
- Source: Binance USD-M daily metrics archives already enumerated by Phase63 train-only audit.
- Fields only: `sum_toptrader_long_short_ratio` (position-weighted top traders) and `count_toptrader_long_short_ratio` (top-trader account count).
- Raw hourly feature per symbol: `log(sum_toptrader_long_short_ratio / count_toptrader_long_short_ratio)`.
- Trading feature: raw feature shifted exactly one hour (`t-1`) before cross-sectional mapping.
- Portfolio mapper: reuse Phase31 cross-sectional mapper unchanged.
- Alpha gross budget: 0.20.
- Missing/blank/nonfinite/nonpositive observations: missing; no fill, proxy, interpolation, smoothing or alternate field.
- Archive integrity: SHA256 checksum + ZIP CRC required for every consumed archive.
- No grid, threshold sweep, sign flip, smoothing sweep, field substitution, regime retuning or parameter search.
- Selection and diagnostics are chronological train-only through Phase63 `train_end`.
- Gate: same Phase47 temporal-fold stability diagnostic under severe costs; PASS only if its existing `stable_train` criterion passes. Supersevere/regime/benchmark gates remain downstream only after a train pass/freeze.
- Holdout is not listed, parsed, inspected or used in this phase.
- V16 Frozen and V99 Frozen are immutable.

## Decision rule
PASS -> freeze the exact Phase67 specification before any untouched-holdout evaluation. FAIL -> reject permanently; no sign/field/smoothing/threshold rescue.
