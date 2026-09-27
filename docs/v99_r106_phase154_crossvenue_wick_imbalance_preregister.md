# V99 R106 Phase154 — Cross-Venue Wick-Imbalance Divergence — PREREGISTERED

Status: PREREGISTERED BEFORE ANY PHASE154 PNL.

## Motivation
Phase153 is an independent range-expansion hypothesis and remains fail-closed under its frozen 98% aligned-coverage contract. Phase154 is prepared without inspecting any Phase154 PnL and changes the economic observable: intrabar rejection asymmetry rather than range magnitude, gap, close location, or directional efficiency.

## Frozen hypothesis
For each mapped OKX/Binance perpetual and completed hour t:
- range_v(t) = high_v(t) - low_v(t), strictly positive and finite.
- upper_wick_v(t) = high_v(t) - max(open_v(t), close_v(t)).
- lower_wick_v(t) = min(open_v(t), close_v(t)) - low_v(t).
- wick_imbalance_v(t) = (upper_wick_v(t) - lower_wick_v(t)) / range_v(t).
- Values are missing if OHLC is non-finite, range is non-positive, or either wick is negative; no epsilon, clipping, repair, interpolation, ffill/bfill, or zero replacement.
- divergence(t) = wick_imbalance_OKX(t) - wick_imbalance_Binance(t).
- Robust normalization is Exact-MAD over the preceding 168 completed hours only, excluding t.
- Cross-sectional centering is applied after robust normalization.
- Direction is REVERSION and is frozen before PnL.
- Complete tradable score is shifted by exactly one hour before target return multiplication.

## Integrity / selection contract
- Source universe, mappings and Phase136 source hashes must reproduce exactly.
- Minimum aligned valid coverage: 98% per required asset; fail closed.
- No interpolation, ffill/bfill, clipping, epsilon, zero replacement, sign flip, grid search, rescue, or post-result direction change.
- Selection and diagnostics are chronological TRAIN-only; four temporal folds required.
- HOLDOUT rows used for feature construction = 0; HOLDOUT rows used for selection = 0.
- Portfolio gross L1 <= 1 after t-1 shift.
- V16 Frozen and V99 Frozen are read-only and must remain byte-identical.

## Gate
TRAIN alpha must satisfy the existing stable-train gate and healthy-fold requirements. Failure is permanent for this exact hypothesis. PASS only then unlocks severe/supersevere costs, regime matrix, tails/concentration, benchmark envelope, reproducibility and eventually the untouched holdout according to the existing protocol.

## Scientific distinction
Phase153 asks whether venue-specific volatility/range expansion relative to each venue's own causal baseline mean-reverts cross-venue. Phase154 asks whether disagreement in intrabar rejection geometry — upper versus lower wick pressure normalized only by the same bar's range — mean-reverts. It does not reuse Phase153's range-expansion observable or tune its window/direction.
