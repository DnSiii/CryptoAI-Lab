# V99 R106 Phase156 — Cross-Venue Body-Fraction Divergence — Preregister

## Scientific hypothesis
A venue-relative candle body fraction may contain cross-venue microstructure information not captured by Phase149-155. For each venue and asset compute `(close-open)/(high-low)` only on finite strictly-positive ranges. Define divergence as OKX minus Binance.

## Frozen direction and construction
- Direction: **REVERSION**.
- Universe: same five Phase136 cross-venue instruments and Binance mappings.
- No imputation, epsilon, clipping, sign flip, rescue, or parameter search.
- Cross-sectional demean each hour after robust normalization.
- Exact rolling MAD normalization with **168h** lookback; normalizer history excludes the current hour.
- Final complete score is shifted by exactly one hour (`t-1`) before portfolio weights.
- L1 gross target <= 1; alpha sleeve gross multiplier 0.20.

## Data/integrity gates
- Reproduce all Phase136 normalized OKX hashes exactly.
- Per-venue valid coverage >= **98%** and aligned valid coverage >= 98% for every asset; otherwise fail closed.
- Invalid bars are never imputed.

## Evaluation contract
- TRAIN only for construction/selection; holdout rows used for feature construction = 0 and selection = 0.
- Four temporal folds required; no fold redefinition after seeing PnL.
- First gate is the existing stable TRAIN diagnostic. A failure is permanent for this hypothesis.
- PASS only: severe and supersevere costs, regime matrix, tails/concentration, benchmark envelope, and reproducibility/invariant checks in that order.
- V16 Frozen and V99 Frozen must remain untouched.

This preregistration is committed before any Phase156 PnL is observed.