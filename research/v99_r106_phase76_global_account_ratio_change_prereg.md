# V99 R106 Phase76 — Global Account Long/Short Ratio Change (TRAIN-ONLY) Preregistration

## Purpose
Phase75 rejected the broad/global account-ratio level hypothesis (TRAIN ROI -29.22%, PF 0.928, 0/4 healthy folds). Phase76 does not rescue, flip, blend, or retune Phase75. It tests the distinct dynamic mechanism of completed-hour repositioning in the same broad account population. This is the pre-specified complement to the level test and mirrors the level-vs-change separation previously applied to top-trader positioning without using any Phase75 sign reversal.

## Locked hypothesis before execution
For each symbol/hour, consume only native `count_long_short_ratio`. Let `z_t = log(count_long_short_ratio_t)`. Define `feature_t = (z_t - z_{t-1}).shift(1)`.

Direction is continuation: symbols with a larger completed-hour increase in global account long/short ratio rank above symbols with a smaller increase/decrease. Use the existing Phase31 deterministic cross-sectional mapper. Gross sleeve allocation is fixed at 0.20.

Single one-hour change hypothesis only. No sign flip, alternate horizon, level blend, top-trader blend, smoothing, threshold, winsorization, imputation, field substitution, parameter grid, or post-result rescue is permitted. Rejection is final for this exact hypothesis.

## Causality / integrity discipline
- Official Binance USD-M daily metrics archives audited in Phase63 only.
- Consume dates only through registered `train_end`; do not list, download, parse, summarize, or inspect holdout metrics or holdout returns.
- Every ZIP must pass official SHA256 CHECKSUM and ZIP CRC.
- Missing archives remain missing; blank/nonfinite/nonpositive observations remain missing; no forward fill.
- Compute the one-hour log change only from observed consecutive hourly values, then shift one full hour (`t-1`) before target construction; do not bridge missing hours.
- Chronological train-only selection uses locked Phase47 temporal folds and severe transaction cost.
- V16 Frozen and V99 Frozen remain read-only.

## Gate
PASS only if `stable_train` is true. PASS freezes this exact specification before supersevere-cost, regime-matrix, benchmark-envelope and eventual untouched-holdout gates. FAIL permanently rejects Phase76 with no retuning.
