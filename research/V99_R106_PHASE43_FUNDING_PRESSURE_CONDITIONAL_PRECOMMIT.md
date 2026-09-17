# V99 R106 Phase43 — Funding-pressure conditional alpha precommit

Status: PRECOMMITTED BEFORE RESULTS. Diagnostic only; no V99/V16 Frozen changes.

## Rationale
Phase37 showed funding-pressure change had comparatively low tail concentration but failed the absolute temporal-stability gate. Phase42 showed funding-vs-price divergence could produce positive aggregate severe-cost ROI, especially at 168v720h, but still failed 0/4 healthy folds because robust mean excluding top 1% remained negative. The next test must therefore be structural rather than a horizon/threshold retune.

## Hypothesis
Funding crowding should only be faded when price action confirms exhaustion. Use the already-defined causal funding-pressure reversal score, but gate exposure by lagged price trend having the SAME sign as the funding-pressure change (crowding and price stretched together). This tests a conditional interaction, not another standalone horizon sweep.

## Fixed families
- funding_exhaustion_24v168h
- funding_exhaustion_72v336h
- funding_exhaustion_168v720h

For each family at hour t: funding is forward-filled then shifted by one hour; fast-minus-slow funding pressure is computed only from known t-1 information; lagged price return over the fast horizon is shifted by one hour. Exposure is contrarian to funding pressure only where sign(funding pressure) == sign(lagged price return); otherwise zero. Cross-sectional portfolio construction reuses the existing deterministic Phase31 weights implementation.

## Discipline / gates
- causal t-1 features only;
- no parameter grid and no post-result threshold tuning;
- chronological train-only family selection;
- untouched holdout cannot affect family selection;
- severe cost is the selection cost;
- minimum 720 active train hours, 120 per temporal fold, 240 holdout hours;
- train: ROI > 0, PF > 1.08, robust mean without top 1% > 0;
- temporal stability: >=3 valid folds and >=3 healthy folds, where healthy requires ROI > 0, PF > 1, robust mean without top 1% > 0;
- holdout is inspected only for a train-selected stable family and requires ROI > 0, PF > 1.05, robust mean without top 1% > 0;
- if no family passes train stability, holdout remains uninspected/descriptive empty and Phase43 is rejected;
- no strategy change in Phase43; any later candidate still owes supersevere costs, regime matrix, benchmark envelope and launch gates.

V16 Frozen and V99 Frozen remain immutable.
