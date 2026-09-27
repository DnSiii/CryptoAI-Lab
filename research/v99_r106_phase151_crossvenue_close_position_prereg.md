# V99 R106 Phase151 — Cross-Venue Close-Position Divergence — Preregistration

## Scientific status
Preregistered after Phase150 TRAIN result was observed and Phase150 was definitively rejected. This is a scientifically distinct successor, not a rescue, sign flip, or reinterpretation of Phase150.

## Hypothesis
Venue disagreement in where the close lands inside each venue's contemporaneous high-low range may encode auction-location disagreement without using prior-close gap mechanics.

For venue v and asset i at hour t:
- RANGE_v(i,t) = high_v(i,t) - low_v(i,t)
- CLPOS_v(i,t) = (close_v(i,t) - low_v(i,t)) / RANGE_v(i,t)
- divergence_i,t = CLPOS_OKX(i,t) - CLPOS_BINANCE(i,t)

RANGE <= 0 or any non-finite required input is missing. No epsilon, clipping, candle repair, forward/back fill, proxy, or imputation.

## Frozen alpha contract
- direction: REVERSION, fixed before PnL
- normalization: rolling Exact-MAD, 168h
- complete score/portfolio shift: t-1 (1 hour)
- deterministic cross-sectional centering and L1 normalization from the Phase144-150 family
- gross L1 <= 1
- chronological TRAIN-only selection
- 4 temporal TRAIN folds
- holdout rows used for feature construction = 0
- holdout rows used for selection = 0
- no sign flip, no grid, no rescue variant

## Data gate
Direct OKX and Binance OHLC only. Require aligned valid coverage >= 98% per preregistered asset. Preserve Phase136 source-hash invariants where applicable. Any violation is DATA_INADMISSIBLE, never a reason to alter the feature.

## Gate sequence
1. TRAIN alpha gate: fold stability plus robust mean excluding top 1%.
2. Only if TRAIN passes: severe and supersevere transaction-cost stress.
3. Only if costs pass: regime matrix plus tails/concentration/pathology audit.
4. Benchmark envelope.
5. Reproducibility/invariant rerun.
6. Holdout remains untouched until formal freeze under the existing project protocol.

## Frozen assets
V16 Frozen and V99 Frozen must not be modified.
