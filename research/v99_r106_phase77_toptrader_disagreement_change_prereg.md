# V99 R106 Phase77 — Top-Trader Disagreement Change (TRAIN-ONLY) Preregistration

## Decision context
Phase76 rejected the global account-ratio change hypothesis on train-only evidence (ROI -31.64%, PF 0.915, 0/4 healthy temporal folds, robust mean excluding top 1% negative). Holdout was not parsed. Phase77 is a distinct dynamic disagreement mechanism, not a sign flip, blend, parameter rescue, or retune of Phase76 or Phase67.

## Locked hypothesis before execution
For each symbol/hour consume only native `sum_toptrader_long_short_ratio` and `count_toptrader_long_short_ratio`. Let `d_t = log(sum_toptrader_long_short_ratio_t / count_toptrader_long_short_ratio_t)`. Define `feature_t = (d_t - d_{t-1}).shift(1)`.

Direction is continuation: symbols whose completed-hour position-weighted top-trader stance becomes more long relative to top-trader account breadth rank above symbols whose disagreement moves the other way. Reuse the Phase31 deterministic cross-sectional mapper unchanged. Gross sleeve allocation is fixed at 0.20.

Single one-hour disagreement-change hypothesis only. No sign flip, alternate horizon, level blend, account/global ratio blend, smoothing, threshold, winsorization, imputation, field substitution, parameter grid, or post-result rescue is permitted. Phase67's disagreement level remains rejected; this tests only its pre-decision dynamic/change mechanism. Rejection is final for this exact hypothesis.

## Causality / integrity discipline
- Official Binance USD-M daily metrics archives already audited in Phase63 only.
- Consume dates only through registered `train_end`; do not list, download, parse, summarize, or inspect holdout metrics or holdout returns.
- Every ZIP must pass official SHA256 CHECKSUM and ZIP CRC.
- Missing archives remain missing; blank/nonfinite/nonpositive observations remain missing; no forward fill.
- Compute disagreement only when both native fields are present in the same observed hour; compute its one-hour change only across adjacent observed hours; then shift one full hour (`t-1`) before target construction. Never bridge a missing hour.
- Chronological train-only selection uses locked Phase47 temporal folds and severe transaction cost.
- V16 Frozen and V99 Frozen remain read-only.

## Gate
PASS only if existing `stable_train` is true. PASS freezes this exact specification before supersevere-cost, regime-matrix, benchmark-envelope and eventual untouched-holdout gates. FAIL permanently rejects Phase77 with no retuning.
