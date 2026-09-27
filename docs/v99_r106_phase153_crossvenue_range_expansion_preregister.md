# V99 R106 Phase153 — Cross-Venue Range-Expansion Divergence — PREREGISTERED

Status: PREREGISTERED BEFORE ANY PHASE153 PNL.

## Motivation
Phase152 range-efficiency reversion failed decisively on TRAIN (ROI -99.4814%, PF 0.19986, 0/4 healthy folds). Do not tune, sign-flip, rescue, or inspect holdout. Phase153 changes the economic observable rather than parameterizing Phase152: disagreement in *range expansion* across venues, not directional close efficiency.

## Frozen hypothesis
For each mapped OKX/Binance perpetual and hour t:
- true_range_v(t) = max(high-low, abs(high-prev_close), abs(low-prev_close)) for venue v.
- baseline_v(t) = rolling median of true_range_v over the preceding 168 completed hours only (exclude t).
- expansion_v(t) = log(true_range_v(t) / baseline_v(t)) when both are finite and strictly positive; otherwise missing. No epsilon repair.
- divergence(t) = expansion_OKX(t) - expansion_Binance(t).
- robust cross-sectional/temporal normalization uses the same Exact-MAD 168h causal machinery validated in Phase137+.
- direction is REVERSION and is frozen before PnL.
- complete tradable score is shifted by exactly one hour before target return multiplication.

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
Phase152 asked whether cross-venue disagreement in directional close efficiency mean-reverts. Phase153 asks whether venue-specific volatility/range expansion relative to each venue's own causal 168h baseline contains a reversion signal. This is not a threshold/window rescue of Phase152.
