# V99 R106 Phase68 — native taker-flow pressure preregistration

## Decision context
Phase67 is rejected on train-only evidence (0/4 healthy temporal folds; train ROI -3.52%; robust mean excluding top 1% negative). No holdout was inspected. Phase68 is a new single hypothesis based on an orthogonal mechanism — aggressive taker flow — not a rescue or retune of Phase67.

## Hypothesis
Within Binance USD-M native metrics, the taker long/short volume ratio measures contemporaneous aggressive buy-vs-sell pressure. Cross-sectionally stronger taker-long pressure at t-1 may carry short-horizon continuation information at t without using future data.

## Frozen specification before execution
- Source: Binance USD-M daily metrics archives already enumerated by Phase63 train-only audit.
- Field only: `sum_taker_long_short_vol_ratio`.
- Raw hourly feature per symbol: `log(sum_taker_long_short_vol_ratio)`.
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
PASS -> freeze the exact Phase68 specification before any untouched-holdout evaluation. FAIL -> reject permanently; no sign/field/smoothing/threshold rescue.
