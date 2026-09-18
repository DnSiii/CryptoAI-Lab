# V99 R106 Phase70 — native open-interest contract change (pre-registration)

Decision time: after Phase69 was rejected on the train-only gate and before any Phase70 return/PnL relation is computed.

## Why this is distinct
Phase69 tested hourly change in `sum_open_interest_value`, which mechanically mixes changes in outstanding futures quantity with mark-price/value changes. Phase70 isolates the native outstanding-contract quantity `sum_open_interest`; it is therefore a pre-specified decomposition of leverage participation rather than a sign/horizon rescue of Phase69. Phase64's 24h price×positive-OI confirmation is also not reused.

## Single hypothesis
**Contract-participation change:** cross-sectional hourly increases in native outstanding futures quantity may identify assets receiving fresh leveraged participation, with short-horizon continuation value.

Fixed feature per asset: take the last valid native `sum_open_interest` observation in each completed UTC hour, compute `diff(log(sum_open_interest), 1)`, then shift the complete feature by exactly one hour before target construction. Use the existing deterministic Phase31 cross-sectional weight mapper and alpha gross budget 0.20.

No alternate OI field, horizon, sign flip, smoothing, winsor percentile, threshold, gross budget, imputation, or missing-data proxy will be tested in Phase70. Blank, nonfinite, zero or negative observations are missing. Missing archives remain missing.

## Gates
- Native metrics downloads/parsing restricted to <= registered train_end from the completed Phase63 audit. Holdout metrics and holdout returns remain untouched.
- SHA256 and ZIP CRC verification on every archive consumed.
- Causal t-1 feature only.
- Existing severe-cost train gate and chronological temporal-fold stability criteria; selection is train-only.
- A reject is permanent for this specification and cannot be rescued by sign/horizon/field retuning.
- Only a train pass may freeze the exact specification for a separate untouched-holdout gate; only after that may supersevere costs, regime matrix and benchmark envelope be evaluated.

V16 Frozen and V99 Frozen remain read-only.