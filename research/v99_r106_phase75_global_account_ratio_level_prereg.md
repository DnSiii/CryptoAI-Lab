# V99 R106 Phase75 — Global Account Long/Short Ratio Level (TRAIN-ONLY) Preregistration

## Purpose
Phase74 rejected the top-trader account-ratio change hypothesis (TRAIN ROI -21.37%, PF 0.904, 0/4 healthy folds). Phase75 does not rescue, flip, blend, or retune Phase74. The Phase63 audited native schema contains the distinct `count_long_short_ratio` field, representing broad/global account positioning rather than top-trader positioning. This is the next untested atomic positioning field and provides a materially different participant-population mechanism.

## Locked hypothesis before execution
For each symbol/hour, consume only native `count_long_short_ratio`. Let `z_t = log(count_long_short_ratio_t)`. Define `feature_t = z_t.shift(1)`.

Direction is continuation: symbols with higher completed-hour global account long/short ratio rank above symbols with lower ratio. Use the existing Phase31 deterministic cross-sectional mapper. Gross sleeve allocation is fixed at 0.20.

Single one-hour level hypothesis only. No sign flip, alternate horizon, change transform, top-trader blend, smoothing, threshold, winsorization, imputation, field substitution, parameter grid, or post-result rescue is permitted. Rejection is final for this exact hypothesis.

## Causality / integrity discipline
- Official Binance USD-M daily metrics archives audited in Phase63 only.
- Consume dates only through registered `train_end`; do not list, download, parse, summarize, or inspect holdout metrics or holdout returns.
- Every ZIP must pass official SHA256 CHECKSUM and ZIP CRC.
- Missing archives remain missing; blank/nonfinite/nonpositive observations remain missing; no forward fill.
- Completed-hour level is shifted one full hour (`t-1`) before target construction.
- Chronological train-only selection uses locked Phase47 temporal folds and severe transaction cost.
- V16 Frozen and V99 Frozen remain read-only.

## Gate
PASS only if `stable_train` is true. PASS freezes this exact specification before supersevere-cost, regime-matrix, benchmark-envelope and eventual untouched-holdout gates. FAIL permanently rejects Phase75 with no retuning.
