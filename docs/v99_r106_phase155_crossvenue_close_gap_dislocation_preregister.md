# V99 R106 Phase155 — Cross-Venue Close/Gap Dislocation (TRAIN-only)

## Scientific hypothesis
The Phase148–154 family shows that raw intrabar geometry divergence is persistently destructive under fixed reversion. Phase155 therefore tests a distinct cross-venue state variable: whether the venue disagreement in **close location relative to the prior close**, normalized by each venue's own contemporaneous true range, contains a causal reversion signal.

For each asset and venue at hour t:

`gap_location_t = (close_t - close_{t-1}) / TR_t`, where `TR_t = max(high_t-low_t, abs(high_t-close_{t-1}), abs(low_t-close_{t-1}))`.

The cross-venue divergence is `OKX gap_location - Binance gap_location`.

This is not a sign rescue of Phase150: Phase150 isolated the opening gap `(open-prev_close)/TR`; Phase155 measures the completed bar displacement from prior close, which combines gap and intrabar resolution into a different observable.

## Frozen contract before any PnL
- Universe: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT, identical Phase136 cross-venue mapping.
- Data integrity: reproduce Phase136 OKX hashes; Binance comes only from canonical V15 replay; no invalid-bar imputation.
- Minimum valid and aligned coverage: 98% per asset/venue; fail closed otherwise.
- Normalizer: Exact rolling MAD, 168 hours, history shifted one hour so the current divergence cannot enter its own normalizer.
- Cross-sectional demeaning each hour.
- Direction: **REVERSION**, fixed before PnL.
- Entire normalized score shifted by exactly one hour before target construction (`t-1`).
- Gross alpha target 0.20; L1 exposure <= 1.0.
- Chronological TRAIN-only selection; four temporal folds required.
- Holdout rows used for feature construction = 0; holdout rows used for selection = 0; post-TRAIN targets exactly zero.
- No grid search, sign flip, clipping rescue, epsilon denominator rescue, missing-value imputation, or post-result parameter change.
- First gate uses canonical severe costs. PASS only if existing stable_train/fold gate passes unchanged.
- PASS chain: severe -> supersevere -> regime matrix -> tails/concentration -> benchmark envelope -> reproducibility/invariants. FAIL: permanent rejection with no rescue.
- V16 Frozen and V99 Frozen must remain untouched.
