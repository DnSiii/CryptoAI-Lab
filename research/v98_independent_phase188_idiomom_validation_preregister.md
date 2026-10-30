# V98 Independent — Phase188 validation preregistration

Status: PREREGISTERED BEFORE VALIDATION READ.

## Frozen candidate
- Source: Phase187 training-only experiment.
- Frozen specification: `h24_w90_low50`.
- Parameters: momentum horizon 24h; dispersion reference 90d; low-dispersion multiplier 0.50; gross cap and all execution/cost/funding conventions exactly as Phase187.
- No retuning, rescue grid, threshold adjustment, or candidate substitution is allowed after validation is read.

## Isolation
- Engine/namespace: V98 Independent only.
- V16 used for selection: false.
- V99 used for selection: false.
- Final holdout used for selection: false.
- Validation window: 2026-01-01 through 2026-07-31 UTC only.
- Final holdout begins 2026-08-01 UTC and MUST remain unread/unloaded.

## Required evaluation
Run the frozen candidate once on untouched validation with the same realistic base costs/funding and the same severe and supersevere cost schedules used by Phase187. Report total return/CAGR, max drawdown, daily Profit Factor, payoff, win rate, positive/negative days, tails/CVaR, turnover, gross exposure, contribution/concentration by asset, and bull/bear/sideways regime attribution. Preserve causal feature construction and chronological ordering.

## Validation gate
PASS only if all preregistered conditions hold without rescue:
1. base total return > 0 and daily PF > 1.0;
2. severe total return > 0 and severe daily PF > 1.0;
3. supersevere total return > 0 and supersevere daily PF > 1.0;
4. no ruin or exposure/invariant violation;
5. no single-asset pathology: largest absolute contribution share <= 0.60;
6. tails are not singular: top-10 positive-day share < 0.50 and bottom-10 negative-day share < 0.50;
7. at least two of bull/bear/sideways regimes with non-zero observations have non-negative approximate return attribution.

Failure => `REJECT_VALIDATION_NO_RESCUE`. Passing => freeze evidence for a separate final-holdout decision; do not open final holdout in Phase188.

## Reproducibility
The validation report must be generated twice from the same rebuilt validation-only inputs and be byte-identical. Data boundary guards must prove max timestamp < 2026-08-01 UTC before economic evaluation.