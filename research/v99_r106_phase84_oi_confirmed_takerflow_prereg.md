# V99 R106 Phase84 — OI-confirmed taker-flow (contingent preregistration)

Status: **PRE-REGISTERED, NOT AUTHORIZED TO RUN UNLESS PHASE83 FAILS**.

If Phase83 passes, this hypothesis remains dormant. If Phase83 fails, Phase84 tests a genuinely different interaction mechanism rather than another ratio pairing: aggressive taker direction is admitted only to the extent that same-hour futures open interest is expanding, representing new leveraged risk entering with the flow.

## Single hypothesis

For each symbol and completed UTC hour, take the last valid native observations of `sum_taker_long_short_vol_ratio` and `sum_open_interest_value`. Define:

`oi_growth_t = log(sum_open_interest_value_t / sum_open_interest_value_t-1)`

`raw_t = log(sum_taker_long_short_vol_ratio_t) * max(oi_growth_t, 0)`

`feature_t = raw_t-1`

Direction is frozen as **continuation**. Positive taker imbalance confirmed by OI expansion is long; negative taker imbalance confirmed by OI expansion is short. OI contraction contributes zero rather than reversing the economic interpretation. The zero boundary is structural (expansion vs contraction), not an optimized threshold.

This differs from Phase64, which used 24h price direction times 24h OI expansion, and from Phase68/69, which tested taker-flow and OI-change mechanisms separately.

## Frozen implementation choices

- Binance USD-M daily metrics archives only; both fields must be positive finite observations.
- Same-hour pairing required; no forward/back-fill and no crossing missing archives/hours.
- OI growth uses exactly the previous hourly observation; if either adjacent hour is missing, the interaction is missing.
- Causality: shift the completed interaction exactly one hour before target construction.
- Existing Phase31 deterministic cross-sectional weighting; alpha gross **0.20**.
- Existing **severe** per-side cost, frozen chronological train end, temporal folds and robustness gate.
- SHA256 CHECKSUM + ZIP CRC verification for every consumed archive.
- Train-only selection; holdout metrics/returns must not be listed, parsed, loaded or inspected.
- V16 Frozen and V99 Frozen remain untouched.

## Anti-overfit

One hypothesis only. No sign flip, alternate OI horizon, alternate threshold, smoothing, winsorization, alpha-gross grid, weighting grid, symbol rescue, or post-result retuning. FAIL is permanent for this exact Phase84 specification.

## Gate

PASS only if `stable_train` passes under severe costs. PASS freezes the exact specification for supersevere, regime-matrix, benchmark-envelope and reproducibility gates before any untouched holdout access. FAIL means permanent rejection and movement to a distinct mechanism/data family.
