# V99 R106 — Phase169–173 macro failure audit — 2026-09-28

## Scope
Independent TRAIN-only audit after Phase173 rejection. No holdout data were fetched, parsed, inspected, or used. V16 Frozen and V99 Frozen remain read-only.

## Evidence pattern
- Phase169 macro risk impulse: rejected by stable_train; 0/4 healthy temporal folds and negative robust mean after removing top 1% outcomes.
- Phase170 curve/liquidity shock: rejected; 0/4 healthy folds and negative robust-tail mean.
- Phase171 VIX×rates interaction: rejected; 0/4 healthy folds and negative robust-tail mean.
- Phase172 macro shock breadth: rejected despite positive aggregate TRAIN ROI; 0/4 healthy folds and negative robust-tail mean.
- Phase173 macro shock acceleration: rejected with TRAIN ROI 0.4809%, PF 1.0162, 0/4 healthy folds, robust mean without top 1% = -3.8585e-06. Fold 2 was outright negative; folds 1/3/4 had positive headline ROI but all retained negative robust-tail means.

## Failure mechanism
The repeated signature is not simply insufficient gross exposure. Across distinct macro transforms, headline aggregate ROI can be mildly positive while the return distribution becomes negative after removing the best 1% of outcomes, and no temporal fold qualifies as healthy. That is evidence of sparse-tail dependence plus weak temporal generalization, not a stable all-regime alpha.

This rules against further magnitude transforms of the same 5-observation shock family (additional z-score windows, thresholds, weights, sign flips, or grids): those would be rescue/retuning against observed TRAIN failures.

## Scientifically distinct next test
Phase174 is therefore limited to a different question: persistence of *direction* across five finite macro observations. It discards shock magnitude entirely, uses fixed equal weights and no fitted threshold, and remains causal/prior-only. This is intended to test state persistence rather than re-parameterize failed shock magnitude.

## Integrity invariants
- Selection remains chronological TRAIN-only [2021-12-01, 2024-01-18).
- Macro observations are prior-day available and the hourly target receives the additional preregistered t-1 shift.
- Severe costs and existing stable_train temporal-fold/robust-tail gate are unchanged.
- Holdout feature-construction rows = 0; holdout selection rows = 0.
- Any Phase174 FAIL is permanent and cannot authorize parameter rescue.
