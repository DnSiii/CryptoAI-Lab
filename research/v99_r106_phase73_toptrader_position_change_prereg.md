# V99 R106 Phase73 — Top-Trader Position Change (TRAIN-ONLY) Preregistration

## Purpose
Phase72 rejected the static level of top-trader aggregate positioning with 0/4 healthy temporal folds. Phase73 does not rescue that level hypothesis or flip its sign. It tests a distinct economic mechanism: whether *new hourly repositioning* by top traders carries short-horizon cross-sectional continuation information even when the absolute long/short level does not.

## Locked hypothesis before execution
For each symbol/hour, consume only native `sum_toptrader_long_short_ratio`. Let `z_t = log(sum_toptrader_long_short_ratio_t)`. Define the feature as:

`feature_t = (z_t - z_{t-1}).shift(1)`.

Economic direction is continuation: symbols with the largest completed-hour increase in top-trader net-long positioning rank above symbols with the largest decrease. Use the existing Phase31 deterministic cross-sectional mapper. Gross sleeve allocation is fixed at 0.20.

This is a single one-hour repositioning hypothesis. No sign flip, alternate difference horizon, level blend, smoothing, threshold, winsorization, imputation, field substitution, parameter grid, or post-result rescue is permitted. A rejection is final for this exact hypothesis.

## Causality / data discipline
- Native source: official Binance USD-M daily metrics archives already audited in Phase63.
- Consume dates only through the registered `train_end`; do not list, download, parse, summarize, or inspect holdout metrics or holdout returns.
- Every consumed ZIP must pass official SHA256 CHECKSUM and internal ZIP CRC.
- Missing archives remain missing; blank/nonfinite/nonpositive observations remain missing. The hourly difference is valid only when both adjacent hourly observations exist naturally; no forward fill.
- The completed-hour difference is shifted one full hour (`t-1`) before target construction.
- Selection is chronological train-only using the locked Phase47 temporal-fold diagnostic and severe transaction cost.
- V16 Frozen and V99 Frozen remain read-only.

## Gate
PASS only if `stable_train` is true. PASS freezes this exact specification before downstream supersevere-cost, regime-matrix, benchmark-envelope and eventual untouched-holdout gates. FAIL means permanent rejection and continuation to a separately preregistered mechanism, with no retuning of Phase73.