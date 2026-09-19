# V99 R106 Phase72 — Top-Trader Position Level (TRAIN-ONLY) Preregistration

## Purpose
Phase71 rejected standalone top-trader account breadth (0/4 healthy folds). Phase72 tests the remaining atomic top-trader positioning field already present in the Phase63 audited native Binance USD-M metrics: the long/short ratio by top-trader positions. Phase66 tested this field only relative to crowd positioning, and Phase67 tested position-vs-account disagreement; Phase72 isolates the native position ratio itself without reusing either composite.

## Locked hypothesis before execution
For each symbol/hour, consume only native `sum_toptrader_long_short_ratio`. Define

`feature_t = log(sum_toptrader_long_short_ratio_t).shift(1)`.

Economic direction is continuation: symbols where top-trader aggregate positions are more net long rank above symbols where those positions are relatively short. The cross-sectional mapper is the already-existing Phase31 deterministic mapper. Gross sleeve allocation is fixed at 0.20.

No sign flip, alternate horizon, smoothing, threshold, winsorization, imputation, field substitution, parameter grid, or post-result rescue is permitted. A rejection is final for this exact hypothesis.

## Causality / data discipline
- Native source: official Binance USD-M daily metrics archives.
- Consume dates only through the Phase63 audited `train_end`.
- Do not list, download, parse, summarize, or inspect holdout metrics or holdout returns.
- Every consumed ZIP must pass official SHA256 CHECKSUM and internal ZIP CRC.
- Missing archives remain missing; blank/nonfinite/nonpositive observations remain missing.
- Signal is shifted one full hour (`t-1`) before target construction.
- Selection is chronological train-only with the existing temporal-fold diagnostic and severe transaction cost.
- V16 Frozen and V99 Frozen are read-only and must remain untouched.

## Gate
Use the same locked Phase47 temporal diagnostic used by Phases64–71. PASS only if `stable_train` is true. PASS freezes this exact specification before downstream stress/regime/benchmark gates and any untouched-holdout evaluation. FAIL means permanent rejection and continuation to a new preregistered mechanism, with no retuning of Phase72.
