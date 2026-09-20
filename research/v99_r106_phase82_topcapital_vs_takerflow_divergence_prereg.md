# V99 R106 Phase82 — TOP-CAPITAL vs TAKER-FLOW divergence (contingent preregistration)

Status: **PRE-REGISTERED, NOT YET AUTHORIZED TO RUN**.

This hypothesis may be executed only if Phase81 fails its frozen train-only gate. If Phase81 passes, Phase82 remains dormant and must not be used to alter the Phase81 specification.

## Hypothesis

A cross-sectional divergence between top-trader capital positioning and aggressive taker flow may contain incremental information distinct from the already-tested positioning-only and taker-only levels/changes.

For symbol *i* and hour *t*:

`raw_i,t = log(sum_toptrader_long_short_ratio_i,t / sum_taker_long_short_vol_ratio_i,t)`

`feature_i,t = raw_i,t-1`

Direction is frozen as **continuation**: larger positive divergence receives larger long cross-sectional weight; smaller/negative divergence receives larger short weight through the existing Phase31 deterministic cross-sectional weighting function.

## Frozen implementation choices

- Source: Binance USD-M daily metrics archives only.
- Required same-hour fields: `sum_toptrader_long_short_ratio`, `sum_taker_long_short_vol_ratio`.
- Both fields must be positive and finite; otherwise that symbol-hour is missing.
- Hourly value: last valid observation in that UTC hour.
- No forward-fill/back-fill and no crossing missing archives/hours.
- Causality: exactly `shift(1)` before target construction.
- Alpha gross: **0.20**.
- Cost gate: existing **severe** per-side cost from the R106 execution assumptions.
- Selection/evaluation: chronological **train only**, same frozen train end and temporal-fold diagnostic used by Phases64-81.
- Holdout metrics/returns must not be listed, parsed, loaded, inspected, or used.
- Every downloaded archive must pass SHA256 CHECKSUM and ZIP CRC verification.
- V16 Frozen and V99 Frozen remain untouched.

## Anti-overfit constraints

Exactly one hypothesis is authorized. No sign flip, alternate lag/horizon, smoothing, threshold, winsorization, weighting grid, alpha-gross grid, symbol rescue, or post-result retuning is permitted. A FAIL is permanent for this exact Phase82 hypothesis.

## Gate

PASS only if the existing `stable_train` diagnostic passes under severe costs, including the frozen temporal-fold and robustness requirements. On PASS, freeze this exact specification and proceed to supersevere cost, regime matrix, benchmark-envelope and reproducibility gates before any untouched holdout access. On FAIL, reject permanently and move to a genuinely distinct pre-registered mechanism.
