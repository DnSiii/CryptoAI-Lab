# V99 R106 Phase139 — Decision

Status: **PERMANENTLY REJECTED AT TRAIN ALPHA GATE**

Evidence source: `reports/candidate_v99_r106_phase139_crossvenue_volatility_dispersion_train_alpha.json`.

The preregistered RV24 cross-venue volatility-dispersion reversion hypothesis failed the first TRAIN-only alpha gate and is not eligible for rescue, sign flip, threshold/grid search, symbol substitution, selective asset removal, severe/supersevere cost evaluation, regime mining, benchmark-envelope promotion, or holdout inspection.

Observed TRAIN diagnostics: ROI -64.8144%, profit factor 0.72754, max drawdown 65.6125%, positive-hour ratio 42.6577%, robust mean excluding top 1% -8.64296e-05. All four chronological folds were eligible and all four were unhealthy; each fold had negative ROI and PF < 1.

Integrity evidence remained valid: Phase136 source hashes reproduced, complete score shifted exactly t-1, feature inputs strictly pre-TRAIN-end, holdout rows used for feature construction/selection 0/0, max L1 approximately 1, and V16 Frozen / V99 Frozen untouched.

Scientific decision: the failure is broad rather than tail-dependent or fold-localized. Phase139 is therefore permanently rejected under the preregistered anti-overfit contract. Research proceeds to the already-preregistered Phase140 data-admissibility gate; no Phase139 parameter tuning is permitted.
