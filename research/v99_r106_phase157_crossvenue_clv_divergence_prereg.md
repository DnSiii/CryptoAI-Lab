# V99 R106 Phase157 — Cross-Venue Close-Location-Value Divergence

Status: PREREGISTERED BEFORE ANY PHASE157 PNL.

## Scientific hypothesis
Phase156 body-fraction divergence is permanently rejected on TRAIN. Phase157 tests a distinct OHLC microstructure geometry: whether disagreement between venues in where the close lands inside the contemporaneous high-low range contains a causal next-hour reversion signal.

For venue v and hour t:

`CLV_v(t) = (2*close_v(t) - high_v(t) - low_v(t)) / (high_v(t) - low_v(t))`

and the raw cross-venue feature is:

`D(t) = CLV_OKX(t) - CLV_BINANCE(t)`.

This differs from Phase156 `(close-open)/(high-low)`: open is absent and the feature measures close location relative to both range extrema. Direction is frozen as REVERSION before PnL.

## Frozen protocol
- Same five Phase136 cross-venue assets and exact source-integrity hashes.
- No invalid-bar imputation; coverage gate >= 98% per venue/asset; fail closed.
- Zero-range bars are invalid for the feature, not epsilon-filled or clipped.
- Exact causal rolling median/MAD normalizer, 168h lookback; history excludes current hour.
- Complete normalized score shifted by exactly 1 hour before target construction (`t-1`).
- L1 gross exposure <= 1.
- Chronological TRAIN-only selection; four temporal folds.
- Holdout rows used for feature construction = 0; selection = 0.
- No grid search, no sign flip, no rescue, no threshold tuning after PnL.
- V16 Frozen and V99 Frozen are immutable.

## Gates
TRAIN alpha must pass the existing stable-train/fold gate before any severe/supersevere cost, regime matrix, tails/concentration, benchmark-envelope or reproducibility promotion. Failure is permanent and triggers no parameter rescue.
