# V99 R106 Phase78 — native taker-flow CHANGE preregistration

## Decision context
Phase77 is rejected on train-only evidence (0/4 healthy temporal folds; train ROI -16.04%; PF 0.9302; robust mean excluding top 1% negative). No holdout was inspected. Phase78 tests the previously untested first-difference dynamics of aggressive taker flow. Phase68 tested the LEVEL only; this is a distinct precommitted change mechanism, not a sign flip or parameter rescue.

## Hypothesis
Cross-sectionally stronger one-hour change in Binance USD-M taker long/short volume pressure at t-1 may carry short-horizon continuation information at t. The economic mechanism is acceleration/reallocation of aggressive flow rather than its absolute crowding level.

## Frozen specification before execution
- Source: Binance USD-M daily metrics archives enumerated by Phase63 train-only audit.
- Field only: `sum_taker_long_short_vol_ratio`.
- Raw hourly value per symbol: `log(sum_taker_long_short_vol_ratio)`.
- Trading feature: `diff(log(sum_taker_long_short_vol_ratio), 1).shift(1)`.
- Direction: continuation only.
- Portfolio mapper: reuse Phase31 cross-sectional mapper unchanged.
- Alpha gross budget: 0.20.
- Missing/blank/nonfinite/nonpositive observations: missing; no fill, proxy, interpolation or smoothing. A change requires both adjacent observed hours; missing hours are never bridged.
- Archive integrity: SHA256 checksum + ZIP CRC required for every consumed archive.
- No grid, threshold sweep, sign flip, horizon sweep, smoothing sweep, field substitution, regime retuning or rescue.
- Selection and diagnostics are chronological train-only through Phase63 `train_end`.
- Gate: same Phase47 temporal-fold stability diagnostic under severe costs; PASS only if existing `stable_train` criterion passes.
- Supersevere/regime/benchmark gates are downstream only after an exact train freeze.
- Holdout is not listed, parsed, inspected or used in this phase.
- V16 Frozen and V99 Frozen are immutable.

## Decision rule
PASS -> freeze the exact Phase78 specification and evaluate supersevere/regime/benchmark gates before any untouched-holdout evaluation. FAIL -> reject permanently; no sign/horizon/level/smoothing/threshold rescue.
