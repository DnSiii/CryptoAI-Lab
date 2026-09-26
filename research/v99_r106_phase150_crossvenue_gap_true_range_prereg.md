# V99 R106 Phase150 — Cross-Venue Gap / True-Range Divergence — Preregistration

## Scientific status
Preregistered after Phase149 implementation/workflow creation and before any Phase149 PnL is observed. This is a scientifically distinct successor, not a rescue or reinterpretation of Phase149. Phase149's frozen direction and gates may not be changed after its result.

## Hypothesis
Cross-venue disagreement in the opening gap relative to each venue's own prior close and true range may encode venue-specific overnight/hour-boundary repricing distinct from close/body location families.

For venue v and asset i at hour t:
- prev_close_v(i,t) = close_v(i,t-1)
- TR_v(i,t) = max(high-low, abs(high-prev_close), abs(low-prev_close))
- GAPTR_v(i,t) = (open-prev_close) / TR
- divergence_i,t = GAPTR_OKX(i,t) - GAPTR_BINANCE(i,t)

TR <= 0 or any non-finite required input is missing. No epsilon, clipping, candle repair, forward/back fill, proxy, or imputation.

## Frozen alpha contract
- direction: REVERSION, fixed before PnL
- normalization: rolling Exact-MAD, 168h
- complete score/portfolio shift: t-1 (1 hour)
- deterministic cross-sectional centering and L1 normalization from the Phase144-149 family
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
