# V99 R106 Phase71 — Top-Trader Account Breadth (TRAIN-ONLY) Preregistration

## Purpose
Phase70 rejected raw open-interest contract change (0/4 healthy folds). Phase71 moves to a distinct positioning mechanism already present in the audited native Binance USD-M metrics: whether the *breadth of top-trader accounts* is net long versus short. This is not the Phase66 position-vs-crowd dispersion or Phase67 top-trader position-vs-account disagreement; it tests the account cohort ratio itself.

## Locked hypothesis before execution
For each symbol/hour, consume only native `count_toptrader_long_short_ratio`. Define

`feature_t = log(count_toptrader_long_short_ratio_t).shift(1)`.

Economic direction is continuation: symbols where a broader share of top-trader accounts is long rank above symbols where that cohort is relatively short. The cross-sectional mapper is the already-existing Phase31 deterministic mapper. Gross sleeve allocation is fixed at 0.20.

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
Use the same locked Phase47 temporal diagnostic used by Phases64–70. PASS only if `stable_train` is true. PASS freezes this exact specification before any untouched-holdout evaluation. FAIL means permanent rejection and continuation to a new preregistered mechanism, with no retuning of Phase71.
