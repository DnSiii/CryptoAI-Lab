# V98 Independent Phase232 — independent pre-implementation audit

Status: **PASS TO IMPLEMENTATION**. This audit is frozen before any Phase232 result is observed.

## Causal contract
At decision/execution `open(t)`, beta and residual-volatility estimates must use returns ending no later than `open(t-1)`. The market factor at every estimation timestamp is the equal-weight return across the fixed eligible universe at that historical timestamp. Cross-sectional ranking at `t` may use only those lagged estimates. No current-bar close/high/low/funding realization may enter the signal.

## Frozen family
Exactly the preregistered 8 combinations are permitted: beta lookbacks {168,336}h × residual-volatility lookbacks {72,168}h × holding periods {4,12}h, with k=1 extreme on each side. No sign flip, asset deletion, regime filter, threshold rescue, or extra grid point is permitted after observation.

## Portfolio/accounting invariants
The intended book is dollar-neutral at entry, long the low-beta/high-residual-volatility extreme and short the high-beta/low-residual-volatility extreme, gross exposure <=1. Overlapping sleeves must be accounted at portfolio level; turnover costs apply to actual position changes. Funding must remain point-in-time and position-signed. Base/severe/supersevere round-trip cost stresses remain 7/14/28 bp.

## Evaluation invariants
Chronological annual folds remain 2023, 2024, 2025. 2026+ is forbidden. Required decision evidence: annual return, max drawdown, Profit Factor, payoff, win rate, positive days, turnover/cost/funding decomposition, bear/bull/sideways regime returns, tails, asset concentration, deterministic duplicate-run hash and frozen-grid/fold/cost assertions.

## Anti-overfit boundary
Phase231 evidence is admissible only as a family-level rejection and cannot tune Phase232. Phase232 must be rejected without rescue if the preregistered mechanical gate yields no survivor. Any implementation ambiguity must be resolved from this causal/accounting contract, not from observed performance.