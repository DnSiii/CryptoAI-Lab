# V99 R106 Phase87 — OI-confirmed top-capital change (contingent pre-registration)

Status: CONTINGENT PRE-REGISTRATION BEFORE PHASE86 RESULT. Execute only if Phase86 is permanently rejected. V16 Frozen and V99 Frozen remain immutable.

## Hypothesis
A directional change in top-trader position long/short ratio is more informative when accompanied by contemporaneous open-interest expansion, indicating new leveraged capital rather than position reshuffling.

## Frozen transform
Using positive finite same-hour Binance USD-M metrics and adjacent hourly observations:

`raw_t = log(sum_toptrader_long_short_ratio_t / sum_toptrader_long_short_ratio_{t-1}) * max(log(sum_open_interest_value_t / sum_open_interest_value_{t-1}), 0)`

Trading feature: exactly `raw_t.shift(1)`. Direction: continuation. Existing deterministic Phase31 cross-sectional weighting. Gross alpha sleeve 0.20. Existing severe per-side cost.

## Anti-overfit constraints
Single hypothesis; no sign flip, grid, thresholds, smoothing, alternate horizons, rescue, or post-result retuning. Same-hour pair and adjacent-hour changes required. Missing archives not filled; SHA256 + ZIP CRC mandatory. Chronological train-only selection and existing temporal folds. Holdout not listed, parsed, inspected, or optimized.

## Gate
May execute only after Phase86 status is TRAIN_ALPHA_REJECT. Existing Phase47 stability diagnostic decides PASS/FAIL. PASS freezes exact specification for supersevere/regime/benchmark/reproducibility gates before untouched holdout; FAIL is permanent rejection.
