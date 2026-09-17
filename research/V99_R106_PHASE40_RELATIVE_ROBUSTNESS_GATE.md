# V99 R106 Phase 40 — Relative Robustness Gate

Status: PRE-REGISTERED / TRAIN-ONLY / NO PROMOTION

## Purpose
Phase 38/39 established that negative severe-cost mean after removing the best 1% of active returns is not, by itself, a valid absolute rejection rule: V13–V16 all exhibit it. Phase 40 converts that observation into a benchmark-relative diagnostic without relaxing any existing promotion gate.

## Locked scope
- V16 Frozen and V99 Frozen remain untouched.
- No untouched holdout evaluation in this phase.
- All strategy features remain causal t-1.
- Candidate selection remains chronological train-only.
- Existing temporal-fold, severe/supersevere, regime-matrix and benchmark-envelope gates remain mandatory before any promotion.
- This diagnostic cannot rescue a candidate that fails profitability/stability gates.

## Pre-registered relative tail criteria
For an independently generated train-only candidate under severe cost:
1. `top1_share_positive <= benchmark top1_share_positive_min` is a tail-concentration advantage.
2. `mean_without_top1 >= benchmark mean_without_top1_max` is a trimmed-return advantage.
3. Both together constitute `RELATIVE_TAIL_PASS`; one alone is `RELATIVE_TAIL_PARTIAL`; neither is `RELATIVE_TAIL_FAIL`.
4. `RELATIVE_TAIL_PASS` is diagnostic only. It is never sufficient for promotion.

Phase39 locked benchmark envelope:
- top1-share minimum: 0.14272573719016096
- top1-share maximum: 0.20570740269750765
- mean-without-top1 minimum: -0.00018944188749105094
- mean-without-top1 maximum: -0.0001427173801025193

Phase37 funding-pressure sleeves already satisfy both relative tail criteria, but remain unpromoted because prior temporal/profitability gates were not met. No parameters may be tuned using this fact.

## Next research rule
The next alpha hypothesis must be orthogonal and pre-registered from train-side information. Phase37 parameters are frozen as a rejected experiment and must not be tuned toward the relative-tail envelope.