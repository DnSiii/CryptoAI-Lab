# V98 Independent — Phase201 Preregistration

Status: **FROZEN BEFORE RESULTS**

## Hypothesis

A large causal volume shock accompanied by same-direction price displacement contains short-horizon continuation information because urgent flow can persist beyond the first completed bar. This is distinct from Phase200 volatility-compression breakout and Phase199 funding-pressure mean reversion.

## Data firewall

Use only V98 Independent training data already admitted by the project firewall. Selection/evaluation folds remain chronological: 2023, 2024, 2025. Validation and final holdout remain unopened. No V99 evidence, state, reports, parameters, workflows, or paper information may be used.

All features and positions at bar t must use information available no later than completed bar t-1. Any implementation violating this is invalid, not repairable by performance.

## Frozen feature family

For each asset/hour, compute from completed bars only:
- log volume shock z-score versus rolling trailing window W in {72h, 168h};
- trailing price return over displacement horizon D in {3h, 6h};
- shock threshold Z in {2.0, 3.0}.

Signal at t:
- long when volume-z at t-1 >= Z and trailing D-hour return at t-1 > 0;
- short when volume-z at t-1 >= Z and trailing D-hour return at t-1 < 0;
- otherwise flat.

Grid is exactly 2 × 2 × 2 = 8 specifications. Equal risk/notional across simultaneously active assets; no cross-sectional quantiles. Fixed holding horizon: 6h, with no pyramiding for the same asset while an existing signal is active.

## Evaluation contract

Report, for every spec and aggregate/fold where defined:
- net return under base realistic fees/slippage/funding;
- severe and supersevere cost/funding stress;
- max drawdown;
- Profit Factor;
- payoff ratio;
- win rate;
- positive-day fraction;
- trade/activity counts and exposure;
- bull/bear/sideways regime decomposition;
- per-asset concentration;
- best/worst tail contribution and bottom-10 loss concentration.

Zero-activity variants cannot pass. A family is not rescued by inverting a losing signal, widening the grid, changing thresholds, dropping bad folds/assets, or inspecting validation/holdout.

## Promotion discipline

Promotion requires economically positive behavior after base costs, non-pathological drawdown/concentration, evidence across chronological folds rather than one isolated year, and meaningful survival under severe/supersevere stress. Exact gates already enforced by the V98 Independent evaluator must not be weakened.

Execution must be deterministic and reproducible; identical inputs/config/code must produce byte-identical report output (or an explicitly documented deterministic canonicalization if timestamps/metadata would otherwise differ).

If the family fails, record REJECT_FAMILY_NO_RESCUE and move to a scientifically distinct preregistered hypothesis.