# V99 R106 Phase121 — preimplementation audit

Date: 2026-09-23

## Evidence harvested
- The corrected `V99 R106 Phase121 Exact Quantile Invariant` workflow completed successfully at commit `380cba133cbb4bfe658bc5e8d62822c64f6ac5c3` (run 17994535925).
- Therefore the exact causal rolling-quantile primitive is infrastructure-ready; this is not evidence for alpha.

## Frozen scientific contract
Phase121 remains exactly the preregistered large-trade pressure hypothesis: 30-day trailing q90 threshold, computed from history strictly before bucket t; buy/sell pressure only among trades whose quote notional exceeds that threshold; signal is lagged t-1 before execution. No sign flip, horizon search, threshold grid, or post-PnL universe changes are permitted.

## Phase120 failure-mechanism carry-forward
Phase120 failed broadly (ROI -99.38%, PF 0.158, max DD 99.38%, 0/4 healthy folds). Phase121 is scientifically distinct because it conditions on the upper tail of trade size rather than reusing unconditional taker imbalance. The Phase120 loss must not be used to tune Phase121 parameters.

## Gate order
1. train-only severe-cost alpha gate; 2. temporal folds; 3. supersevere costs; 4. regime matrix; 5. benchmark envelope; 6. reproducibility/invariants. Holdout remains sealed until all preceding gates pass with the frozen specification.

## Integrity requirements
- abort on any source timestamp >= 2024-01-18;
- require >=8 executable assets without selecting on return/PnL;
- verify source ZIP SHA256/CRC and Frozen snapshots before/after;
- deterministic replay and exact quantile self-tests must pass;
- missing data are not silently imputed.

Decision: IMPLEMENT/EXECUTE Phase121 next without scientific parameter changes. V16 Frozen and V99 Frozen remain read-only.
