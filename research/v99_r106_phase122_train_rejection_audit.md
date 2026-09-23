# V99 R106 Phase122 — train rejection audit

Status: PERMANENTLY REJECTED AT MANDATORY PRE-HOLDOUT TRAIN GATE.

## Evidence harvested
The optimized Phase122 run completed successfully as an execution job and persisted its scientific result. The frozen continuation hypothesis produced, under the severe-cost train gate:

- active hours: 18,671
- train ROI: -0.9767994667383862
- profit factor: 0.24623053832949052
- max drawdown (abs): 0.9768149401167731
- positive-hour ratio: 0.24605002410154786
- robust mean excluding top 1%: -0.00021810406046208567
- valid temporal folds: 4
- healthy temporal folds: 0

Fold ROIs were -0.58649, -0.60567, -0.60908, and -0.63604. Profit factor deteriorated from 0.3449 in fold 1 to 0.1817 in fold 4. Every fold's robust mean excluding the top 1% was negative.

## Failure mechanism audit
This is not a tail-only or single-period failure. Losses are broad across all four chronological folds, the top-1%-trimmed mean remains negative in every fold, and PF is far below 1 throughout. The result therefore rejects the frozen continuation interpretation of aggressive trade-count imbalance under the preregistered implementation rather than merely exposing one exceptional crash interval.

The monotonic deterioration in fold PF is descriptive only and MUST NOT be used to tune a time-varying sign, threshold, horizon, or regime switch. A post-result sign flip is explicitly forbidden by the preregistration and would constitute contamination.

## Decision
Phase122 is permanently rejected. Do not run supersevere, regime, benchmark-envelope, or holdout gates for this candidate: the mandatory severe train gate already failed. Do not retune or reverse the exact feature after observing this PnL.

V16 Frozen and V99 Frozen remain read-only. Holdout remains untouched.
