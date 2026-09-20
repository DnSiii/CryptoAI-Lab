# V99 R106 Phase86 — OI / top-capital change dislocation (pre-registration)

Status: PRE-REGISTERED BEFORE EXECUTION. Train-only hypothesis. V16 Frozen and V99 Frozen are immutable.

## Hypothesis
A one-hour change in top-trader position long/short ratio that exceeds the contemporaneous one-hour change in open-interest value represents informed-capital positioning dislocation. Test a single continuation direction: long assets where top-capital positioning strengthens relative to OI growth, short where it weakens.

## Frozen transform
For each symbol/hour t, using Binance USD-M daily metrics and requiring positive finite same-hour values plus adjacent hourly observations:

`raw_t = log(sum_toptrader_long_short_ratio_t / sum_toptrader_long_short_ratio_{t-1}) - log(sum_open_interest_value_t / sum_open_interest_value_{t-1})`

Trading feature is exactly `raw_t.shift(1)` (causal t-1). Cross-sectional weights use the existing Phase31 deterministic weighting routine. Gross alpha sleeve = 0.20. Cost = existing severe per-side cost.

## Anti-overfit constraints
Single hypothesis only. No sign flip, grid, threshold search, horizon search, smoothing, rescue, or post-result retuning. Missing archives are not filled. Every archive must pass SHA256 and ZIP CRC. OI and top-capital observations must be positive/finite and both changes require adjacent hours. Selection and diagnostics are chronological train-only with existing temporal folds. Holdout must not be listed, parsed, inspected, or optimized.

## Gate
Use the existing Phase47 train diagnostic/stability gate. PASS freezes this exact specification for downstream supersevere, regime-matrix, benchmark-envelope, and reproducibility gates before any untouched-holdout access. FAIL is permanent rejection of this exact hypothesis.
