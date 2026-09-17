# V99 R106 Phase 42 — Funding / Price Divergence

Status: PRE-REGISTERED / TRAIN-ONLY SELECTION

Phase41 is rejected: despite positive aggregate train ROI, all fixed Amihud families failed the locked stability criterion with 0/4 healthy folds. Holdout was therefore not inspected for selection.

Hypothesis: lagged funding-pressure change may only contain useful positioning information when it diverges from lagged price trend. This is a fixed interaction mechanism, not tuning of Phase37's rejected standalone funding-pressure sleeves. Crowded funding pressure that is not confirmed by price is treated contrarian.

Locked families: 24h price vs 24v168h funding pressure; 72h price vs 72v336h funding pressure; 168h price vs 168v720h funding pressure. Score is negative standardized cross-sectional funding-pressure change multiplied by the sign/magnitude of disagreement with the matching lagged price return. Fixed TOP_N=2 and alpha gross=0.20.

All inputs t-1 causal. Chronological train-only selection, no parameter grid, severe-cost selection, temporal folds. Holdout only after locked train stability. Any survivor still requires supersevere costs, regime matrix and benchmark envelope before promotion. V16 Frozen and V99 Frozen untouched.