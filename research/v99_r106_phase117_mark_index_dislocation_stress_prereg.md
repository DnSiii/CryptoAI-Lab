# V99 R106 Phase117 — mark/index dislocation-stress quality alpha preregistration

Pre-registered **after Phase116 completed** and **before any Phase117 basis value, return relation or PnL is observed**.

## Evidence permitting the experiment
Phase116 established a causally usable paired source across the complete R106 train interval: all 48 canonical symbols have paired official Binance USD-M mark-price and index-price 1h archives beginning 2021-12-01; 37,069 paired daily files were inventoried; 480 deterministic mark/index file pairs passed SHA256, ZIP CRC, row-shape, finite-OHLC, strict timestamp and exact cross-source timestamp-alignment checks; no holdout market value was parsed.

This source is temporally admissible under the unchanged >=3-valid-fold requirement.

## Distinction from rejected Phase113
Phase113 tested the **signed level** of the Binance premium-index as a crowding-reversal alpha and is permanently rejected. Phase117 does not invert its sign, reuse its feature, or rescue its horizon.

Phase117 instead asks a separate risk-quality question: whether assets whose perpetual **mark price persistently departs from the index in either direction** behave as lower-quality/stressed instruments cross-sectionally. Direction of the mark/index gap is deliberately discarded before scoring.

## Frozen hypothesis
1. Sources: official Binance USD-M `markPriceKlines` and `indexPriceKlines`, interval 1h, canonical PIT48 only.
2. Train content only: 2021-12-01 00:00 UTC <= timestamp < 2024-01-18 00:00 UTC.
3. At each asset/hour compute signed log dislocation `b = log(mark_close / index_close)` only when both closes are finite and positive.
4. Compute **24-hour RMS dislocation stress**: `sqrt(mean(b^2, 24h))`, requiring all 24 hourly observations. Twenty-four hours is fixed ex ante as one complete daily market cycle; there is no horizon grid.
5. Cross-sectionally robust-standardize stress each hour using median/MAD, requiring >=10 simultaneous assets and MAD > 1e-12.
6. Fixed direction: `score = -robust_z(stress)` — long relatively low mark/index dislocation stress, short relatively high dislocation stress. This is a risk-quality hypothesis and does not depend on the sign/result of Phase113.
7. Bound with `tanh`, cross-sectional L1 normalization, fixed alpha gross 0.20.
8. Shift the **complete score exactly one hour (t-1)** before trading.
9. First PnL gate: canonical **severe** execution/cost model.
10. Selection: chronological train only with the existing temporal folds and unchanged `stable_train` gate.
11. Missing archives/hours remain missing; no forward-fill, interpolation, cross-asset imputation, synthetic prehistory or gap reconstruction.

## Deterministic archive contract
- Use checksum-verified official monthly mark/index archives for complete months through 2023-12.
- Use checksum-verified paired daily archives for 2024-01-01 through 2024-01-17.
- Never request a January-2024 monthly archive.
- Defensively discard every parsed timestamp >= 2024-01-18 00:00 UTC.
- If a monthly archive is unavailable, fall back only to Phase116-admitted paired daily dates for that same pre-train month.
- Mark and index timestamps must align before computing any dislocation value.

## Prohibited
No parameter grid, alternative RMS horizon, alternative absolute/signed transform, threshold search, sign flip, rescue pass, selective fold deletion, cost relaxation, retuning, or holdout access after observing the result.

## Decision
PASS only if the existing `stable_train` gate passes unchanged. PASS freezes this exact specification for supersevere cost, regime matrix, benchmark envelope and reproducibility gates before untouched holdout. FAIL permanently rejects this Phase117 specification and moves to a genuinely distinct mechanism.

V16 Frozen and V99 Frozen remain immutable.
