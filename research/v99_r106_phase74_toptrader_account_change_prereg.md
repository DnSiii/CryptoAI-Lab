# V99 R106 Phase74 — Top-Trader Account-Ratio Change (TRAIN-ONLY) Preregistration

## Purpose
Phase73 rejected aggregate top-trader position-ratio change (TRAIN ROI -12.40%, PF 0.947, 1/4 healthy folds). Phase74 does not rescue, flip, blend, or retune Phase73. It tests the complementary breadth mechanism already available in the audited native metrics: whether the completed-hour change in the *count/account* top-trader long/short ratio carries cross-sectional continuation information. This separates broad account participation from aggregate position sizing.

## Locked hypothesis before execution
For each symbol/hour, consume only native `count_toptrader_long_short_ratio`. Let `z_t = log(count_toptrader_long_short_ratio_t)`. Define:

`feature_t = (z_t - z_{t-1}).shift(1)`.

Direction is continuation: symbols with the largest completed-hour increase in top-trader account long/short breadth rank above symbols with the largest decrease. Use the existing Phase31 deterministic cross-sectional mapper. Gross sleeve allocation is fixed at 0.20.

Single one-hour hypothesis only. No sign flip, alternate horizon, level/position-ratio blend, smoothing, threshold, winsorization, imputation, field substitution, parameter grid, or post-result rescue is permitted. Rejection is final for this exact hypothesis.

## Causality / integrity discipline
- Official Binance USD-M daily metrics archives audited in Phase63 only.
- Consume dates only through registered `train_end`; do not list, download, parse, summarize, or inspect holdout metrics or holdout returns.
- Every ZIP must pass official SHA256 CHECKSUM and ZIP CRC.
- Missing archives remain missing; blank/nonfinite/nonpositive observations remain missing. Difference requires naturally adjacent hourly observations; no forward fill.
- Completed-hour difference is shifted one full hour (`t-1`) before target construction.
- Chronological train-only selection uses locked Phase47 temporal folds and severe transaction cost.
- V16 Frozen and V99 Frozen remain read-only.

## Gate
PASS only if `stable_train` is true. PASS freezes this exact specification before supersevere-cost, regime-matrix, benchmark-envelope and eventual untouched-holdout gates. FAIL permanently rejects Phase74 with no retuning.