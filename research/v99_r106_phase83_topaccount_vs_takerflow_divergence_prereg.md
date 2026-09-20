# V99 R106 Phase83 — TOP-ACCOUNT vs TAKER-FLOW divergence

Status: **PRE-REGISTERED AND AUTHORIZED ONLY AFTER PHASE82 REJECTION**.

Phase82 is permanently rejected by its frozen train-only gate. Phase83 is a distinct native-metrics mechanism: it tests whether breadth of top-trader account positioning diverging from aggressive taker flow carries cross-sectional continuation information. It does not retune Phase82.

## Hypothesis

For symbol *i* and hour *t*:

`raw_i,t = log(count_toptrader_long_short_ratio_i,t / sum_taker_long_short_vol_ratio_i,t)`

`feature_i,t = raw_i,t-1`

Direction is frozen as **continuation**: larger positive top-account-vs-taker divergence receives larger long cross-sectional weight; smaller/negative divergence receives larger short weight through the existing Phase31 deterministic cross-sectional weighting function.

This completes a previously untested pairing in the native positioning/flow matrix: Phase79 tested top-account vs global-account positioning; Phase82 tested top-capital vs taker-flow. Phase83 tests top-account breadth vs taker-flow, so it is not a sign/horizon/weight rescue of a rejected specification.

## Frozen implementation choices

- Source: Binance USD-M daily metrics archives only.
- Required same-hour fields: `count_toptrader_long_short_ratio`, `sum_taker_long_short_vol_ratio`.
- Both fields must be positive and finite; otherwise that symbol-hour is missing.
- Hourly value: last valid observation in that UTC hour.
- No forward-fill/back-fill and no crossing missing archives/hours.
- Causality: exactly `shift(1)` before target construction.
- Alpha gross: **0.20**.
- Cost gate: existing **severe** per-side cost from R106 execution assumptions.
- Selection/evaluation: chronological **train only**, same frozen train end and temporal-fold diagnostic used by Phases64-82.
- Holdout metrics/returns must not be listed, parsed, loaded, inspected, or used.
- Every downloaded archive must pass SHA256 CHECKSUM and ZIP CRC verification.
- V16 Frozen and V99 Frozen remain untouched.

## Anti-overfit constraints

Exactly one hypothesis is authorized. No sign flip, alternate lag/horizon, smoothing, threshold, winsorization, weighting grid, alpha-gross grid, symbol rescue, or post-result retuning is permitted. A FAIL is permanent for this exact Phase83 hypothesis.

## Gate

PASS only if the existing `stable_train` diagnostic passes under severe costs, including frozen temporal-fold and robustness requirements. On PASS, freeze this exact specification and proceed to supersevere cost, regime matrix, benchmark-envelope and reproducibility gates before any untouched holdout access. On FAIL, reject permanently and move to a genuinely distinct pre-registered mechanism.
