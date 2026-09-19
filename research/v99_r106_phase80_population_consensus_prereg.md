# V99 R106 Phase80 — cross-population positioning consensus preregistration

## Decision context
Phase79 is permanently rejected on train-only evidence despite positive aggregate ROI: train ROI +8.06%, PF 1.0333, max DD 6.48%, robust mean excluding top 1% negative, and only 1/4 healthy temporal folds. No holdout was inspected. Phase79's disagreement feature will not be sign-flipped, differenced, smoothed, thresholded, or otherwise rescued.

## Hypothesis
A distinct mechanism is **cross-population positioning consensus**: when both Binance USD-M top-trader accounts and the global account population lean in the same directional sense, their parameter-free geometric consensus may contain broader positioning continuation information than either population alone or their disagreement. This is not a retune of Phase79 divergence: the statistic is the log geometric mean of the two positive ratios, not their ratio/difference.

## Frozen specification before execution
- Source: Binance USD-M daily metrics archives enumerated by the Phase63 train-only audit.
- Fields only: `count_toptrader_long_short_ratio` and `count_long_short_ratio`.
- Raw hourly value per symbol: `0.5 * (log(count_toptrader_long_short_ratio) + log(count_long_short_ratio))`, using only positive finite values observed in the same completed hour.
- Trading feature: raw consensus `.shift(1)`.
- Direction: continuation only (larger joint long bias -> larger cross-sectional long weight).
- Portfolio mapper: Phase31 cross-sectional mapper unchanged.
- Alpha gross budget: 0.20.
- Missing/blank/nonfinite/nonpositive observations: missing; no fill, proxy, interpolation or smoothing. Both fields must exist in the same hour.
- Archive integrity: SHA256 checksum + ZIP CRC required for every consumed archive.
- No grid, threshold sweep, sign flip, horizon sweep, smoothing sweep, field substitution, regime retuning, weighting parameter, or rescue.
- Selection and diagnostics are chronological train-only through Phase63 `train_end`.
- Gate: same Phase47 temporal-fold stability diagnostic under severe costs; PASS only if existing `stable_train` criterion passes.
- Supersevere/regime/benchmark gates are downstream only after an exact train freeze.
- Holdout is not listed, parsed, inspected or used in this phase.
- V16 Frozen and V99 Frozen are immutable.

## Decision rule
PASS -> freeze the exact Phase80 specification and evaluate supersevere/regime/benchmark gates before any untouched-holdout evaluation. FAIL -> reject permanently; no sign/horizon/weight/smoothing/threshold rescue.
