# V99 R106 Phase149 — Cross-Venue True-Range Location Divergence — Preregistration

## Scientific status
Preregistered after Phase148 TRAIN_ALPHA_REJECT and before any Phase149 PnL is observed. Phase148 is permanently rejected; no sign flip, rescue, parameter grid, or reinterpretation is permitted.

## Hypothesis
Cross-venue disagreement in where the close sits inside a true-range-normalized candle may contain information distinct from the already rejected close-location, raw range-intensity, body-intensity, wick-imbalance, and body/range-ratio families.

For venue v and asset i at hour t:
- prev_close_v(i,t) = close_v(i,t-1)
- TR_v(i,t) = max(high-low, abs(high-prev_close), abs(low-prev_close))
- TL_v(i,t) = (close-open) / TR
- divergence_i,t = TL_OKX(i,t) - TL_BINANCE(i,t)

TR <= 0 or non-finite inputs are missing. No epsilon, clipping, candle repair, forward/back fill, proxy, or imputation.

## Frozen alpha contract
- direction: REVERSION, fixed before PnL
- normalization: rolling Exact-MAD, 168h, same causal implementation family as Phases144-148
- complete score/portfolio shift: t-1 (1 hour)
- cross-sectional construction and portfolio normalization: same deterministic Phase144-148 machinery
- gross L1 <= 1
- chronological TRAIN-only selection
- 4 temporal TRAIN folds
- holdout rows used for feature construction = 0
- holdout rows used for selection = 0
- no sign flip, no grid, no rescue variant

## Data gate
Use direct OHLC from OKX and Binance only. Require aligned valid coverage >= 98% per preregistered asset. Preserve Phase136 source-hash invariants where applicable. Any violation is DATA_INADMISSIBLE, not a reason to alter the feature.

## Gate sequence
1. TRAIN alpha gate with fold stability and robust mean excluding top 1%.
2. Only if TRAIN passes: severe and supersevere transaction-cost stress.
3. Only if costs pass: regime matrix plus tails/concentration/pathology audit.
4. Benchmark envelope.
5. Reproducibility/invariant rerun.
6. Holdout remains untouched until a candidate is formally frozen under the existing project protocol.

## Frozen assets
V16 Frozen and V99 Frozen must not be modified.
