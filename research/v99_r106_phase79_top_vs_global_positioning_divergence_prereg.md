# V99 R106 Phase79 — top-vs-global positioning divergence preregistration

## Decision context
Phase78 is rejected on train-only evidence (0/4 healthy temporal folds; train ROI -27.26%; PF 0.8909; robust mean excluding top 1% negative). No holdout was inspected. The direct native levels/changes tested through Phase78 have not produced stable train evidence, so Phase79 moves to a precommitted cross-population disagreement mechanism rather than retuning a failed sign, horizon, threshold, or smoothing parameter.

## Hypothesis
When Binance USD-M top-trader accounts are more net-long (or less net-short) than the global account population at t-1, the cross-sectional disagreement may identify informed-positioning continuation at t. This tests segmentation between participant populations, not the absolute level or first difference of either population alone.

## Frozen specification before execution
- Source: Binance USD-M daily metrics archives enumerated by Phase63 train-only audit.
- Fields only: `count_toptrader_long_short_ratio` and `count_long_short_ratio`.
- Raw hourly value per symbol: `log(count_toptrader_long_short_ratio / count_long_short_ratio)` using only positive finite values observed in the same completed hour.
- Trading feature: raw divergence `.shift(1)`.
- Direction: continuation only (larger top-vs-global long bias -> larger cross-sectional long weight).
- Portfolio mapper: reuse Phase31 cross-sectional mapper unchanged.
- Alpha gross budget: 0.20.
- Missing/blank/nonfinite/nonpositive observations: missing; no fill, proxy, interpolation or smoothing. Both fields must exist in the same hour.
- Archive integrity: SHA256 checksum + ZIP CRC required for every consumed archive.
- No grid, threshold sweep, sign flip, horizon sweep, smoothing sweep, field substitution, regime retuning or rescue.
- Selection and diagnostics are chronological train-only through Phase63 `train_end`.
- Gate: same Phase47 temporal-fold stability diagnostic under severe costs; PASS only if existing `stable_train` criterion passes.
- Supersevere/regime/benchmark gates are downstream only after an exact train freeze.
- Holdout is not listed, parsed, inspected or used in this phase.
- V16 Frozen and V99 Frozen are immutable.

## Decision rule
PASS -> freeze the exact Phase79 specification and evaluate supersevere/regime/benchmark gates before any untouched-holdout evaluation. FAIL -> reject permanently; no sign/horizon/level/smoothing/threshold rescue.
