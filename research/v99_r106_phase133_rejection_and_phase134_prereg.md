# V99 R106 — Phase133 rejection / Phase134 preregistration

## Phase133 decision
Phase133 Idiosyncratic Residual Dispersion Continuation is permanently rejected at the preregistered severe train-only gate. Aggregate severe ROI was -49.1574%, PF 0.7067, max drawdown 49.1934%, robust mean excluding top 1% hours -4.8736e-05/hour, with 0/4 healthy chronological folds. Causality invariants passed and the holdout was not parsed. No sign flip, window tuning, threshold search, or repair is permitted.

## Failure-family audit
Phases126–133 establish a broad negative result for direct hourly cross-sectional price/volatility transforms under severe friction: momentum, residual momentum, volatility normalization, short reversal, semivariance, idiosyncratic volatility shocks, vol-of-vol and residual dispersion all failed temporal stability. Continuing to mutate price-only transforms would spend degrees of freedom on the same information family.

## Phase134 — Dollar-Volume Surprise Continuation
Preregistered before any Phase134 PnL is computed.

Scientifically distinct information object: traded dollar volume, not return direction or volatility geometry.

Single frozen hypothesis:
- inputs: hourly close and volume already present in the canonical futures dataset, train-only; no holdout parsing;
- dollar volume DV_t = close_t * volume_t;
- feature: log((rolling 24h mean DV + eps)/(own trailing 168h rolling median of the 24h mean DV + eps));
- transform: cross-sectional robust median/(1.4826*MAD), requiring at least 8 assets;
- direction: continuation — unusually elevated relative participation receives positive score, unusually compressed participation negative score;
- bounded score tanh(z);
- execution causality: shift complete score exactly one hour (t-1);
- normalize each hour to L1=1, fixed alpha sleeve gross 0.20;
- severe cost gate first, four chronological temporal folds, robust mean excluding top 1% hours;
- no grid, no alternative windows, no sign flip, no threshold search, no post-result repair.

Frozen windows: DV mean 24h; own baseline 168h. Decision gate is the existing stable-train diagnostic. PASS freezes the exact specification for supersevere, regime matrix, tails/concentration, benchmark envelope and reproducibility before untouched holdout. FAIL is permanent.

Integrity requirements unchanged: V16 Frozen and V99 Frozen SHA snapshots before/after execution, chronological train-only selection, t-1, post-train targets exactly zero, untouched holdout.