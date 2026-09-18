# V99 R106 Phase46 decision

Decision: **REJECT / no promotion**.

Phase46 tested a pre-registered, causal t-1, threshold-free cross-sectional funding-level crowding hypothesis using 24h, 72h and 168h smoothing. Selection remained chronological and train-only; V16 Frozen and V99 Frozen were not modified.

Although the 72h and 168h sleeves produced positive aggregate severe-cost train ROI (+48.04% and +45.21%), all three sleeves failed the pre-registered stability gate: 0/4 healthy temporal folds and negative robust mean after removing the top 1% return tail. The 24h sleeve also failed with 0/4 healthy folds. Therefore no sleeve is eligible for holdout selection or downstream supersevere/regime/benchmark promotion gates.

This result is treated as evidence that raw funding-level crowding contains some aggregate gross structure but is too tail-dependent and temporally unstable under the current severe-cost implementation. No threshold/horizon tuning is authorized from this evidence. Any next experiment must use a distinct pre-registered mechanism rather than optimize Phase46 against these outcomes.
