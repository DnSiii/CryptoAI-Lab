# V99 R106 Phase85 — OI-contraction taker-flow absorption (contingent preregistration)

Status: **PRE-REGISTERED, AUTHORIZED ONLY AFTER PHASE84 TRAIN_ALPHA_REJECT**.

Phase84 rejected the hypothesis that aggressive taker imbalance accompanied by expanding open interest should continue. Phase85 moves to the economically distinct liquidation/position-closing state that Phase84 deliberately zeroed out: aggressive taker imbalance while aggregate futures open interest contracts. The hypothesis is that, when risk is leaving rather than entering, the aggressive flow is more likely forced closing/liquidation and therefore should be faded rather than followed.

## Single hypothesis

For each symbol and completed UTC hour, using native Binance USD-M daily metrics observations:

`oi_growth_t = log(sum_open_interest_value_t / sum_open_interest_value_t-1)`

`contraction_t = max(-oi_growth_t, 0)`

`raw_t = -log(sum_taker_long_short_vol_ratio_t) * contraction_t`

`feature_t = raw_t-1`

Direction is frozen as **contrarian/absorption**: buy-dominant taker flow during OI contraction maps short; sell-dominant taker flow during OI contraction maps long. OI expansion contributes zero. The zero boundary is structural (risk entering vs leaving), not an optimized threshold.

This is not a sign flip of Phase84 on the same sample: Phase84's admissible state was OI expansion only and its contraction observations were exactly zero. Phase85 evaluates the mutually exclusive OI-contraction state with a liquidation/closing-risk economic mechanism. It also differs from Phase62 taker absorption, which used price-response inefficiency rather than OI contraction.

## Frozen implementation choices

- Binance USD-M daily metrics archives only; `sum_taker_long_short_vol_ratio` and `sum_open_interest_value` must be positive finite observations.
- Same-hour pairing required; no forward/back-fill and no crossing missing archives/hours.
- OI growth uses exactly the previous hourly observation; if either adjacent hour is missing, the interaction is missing.
- Causality: shift the completed interaction exactly one hour before target construction.
- Existing Phase31 deterministic cross-sectional weighting; alpha gross **0.20**.
- Existing **severe** per-side cost, frozen chronological train end, temporal folds and robustness gate.
- SHA256 CHECKSUM + ZIP CRC verification for every consumed archive.
- Train-only selection; holdout metrics/returns must not be listed, parsed, loaded or inspected.
- V16 Frozen and V99 Frozen remain untouched.

## Anti-overfit

One hypothesis only. No alternate sign, OI horizon, contraction threshold, smoothing, winsorization, alpha-gross grid, weighting grid, symbol rescue, regime rescue, or post-result retuning. FAIL is permanent for this exact Phase85 specification.

## Gate

PASS only if `stable_train` passes under severe costs. PASS freezes the exact specification for supersevere, regime-matrix, benchmark-envelope and reproducibility gates before any untouched holdout access. FAIL means permanent rejection and movement to a distinct mechanism/data family.