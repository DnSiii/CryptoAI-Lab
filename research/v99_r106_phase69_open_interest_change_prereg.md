# V99 R106 Phase69 — native open-interest change preregistration

## Decision context
Phase68 is rejected on train-only evidence (0/4 healthy temporal folds; train ROI -23.64%; PF 0.906; robust mean excluding top 1% negative). No holdout was inspected. Phase69 is a new single hypothesis based on an orthogonal mechanism — cross-sectional capital/positioning expansion measured by native open-interest change — not a rescue, sign flip, or retune of Phase68.

## Hypothesis
Within Binance USD-M native metrics, `sum_open_interest_value` measures aggregate notional open interest. Cross-sectionally stronger positive one-hour log change in open-interest value at t-1 may identify symbols receiving fresh positioning/capital and carry short-horizon continuation information at t without future data.

## Frozen specification before execution
- Source: Binance USD-M daily metrics archives already enumerated by Phase63 train-only audit.
- Field only: `sum_open_interest_value`.
- Raw hourly level per symbol: `log(sum_open_interest_value)`.
- Raw change feature: one-hour first difference of the log level.
- Trading feature: raw change shifted exactly one hour (`t-1`) before cross-sectional mapping.
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
PASS -> freeze the exact Phase69 specification before any untouched-holdout evaluation. FAIL -> reject permanently; no sign/field/smoothing/threshold rescue.
