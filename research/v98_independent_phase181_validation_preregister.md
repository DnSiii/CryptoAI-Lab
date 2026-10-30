# V98 Independent — Phase181 validation preregistration

Preregistered only after Phase180 was frozen PASS_TRAINING_FREEZE_FOR_VALIDATION.

## Purpose
Perform a single untouched validation of the exact Phase180 candidate. This phase is confirmatory, not exploratory.

## Frozen candidate
- Signal family: T10YIE.
- Transformation: 63 observations, identical to Phase180.
- Availability: next US business day; same-day use forbidden.
- Exposure: exactly 0.50 when the frozen disinflation-stress condition is active, otherwise 1.00.
- Universe/engine: identical V98 Independent frozen stack used by Phase180.
- Costs/funding: identical base, severe and supersevere schedules already frozen in V98 Independent.
- No parameter, threshold, lookback, asset, cost, regime or date sweep.
- No rescue after validation inspection.

## Isolation
Validation interval must be the pre-existing V98 Independent validation interval from the frozen research protocol; this preregistration does not redefine dates. Final holdout remains unopened and must not be loaded, summarized, hashed for performance inspection, or used for selection. V16 and V99 remain prohibited.

## Required outputs
CONTROL and frozen candidate: total return/CAGR, max drawdown, Profit Factor, payoff, win rate, positive/negative days, severe/supersevere performance, ruin flag, turnover, chronological subfolds if the frozen validation protocol defines them, regime attribution, per-asset contribution, concentration, tails, max open gross/path gross, and deterministic reproducibility/invariants.

## Decision rule
Use the already-frozen V98 Independent validation gates without relaxation. PASS only if every mandatory validation gate passes under the exact candidate and required cost stresses. Any mandatory failure => REJECT_VALIDATION_NO_RESCUE. A pass freezes the candidate for the subsequent final-holdout procedure; it does not authorize tuning or immediate holdout inspection in the same decision record.
