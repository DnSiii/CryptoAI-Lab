# V98 Independent — Phase150 preregistration (WTI risk-off)

Status: PREREGISTERED BEFORE ECONOMIC INSPECTION.
Dependency: Phase149 must be PASS_DATA_ONLY with frozen DCOILWTICO hash. No crypto-return relationship was inspected to define this hypothesis.

## Hypothesis
A sustained rise in spot WTI is an exogenous inflation/financial-conditions pressure proxy. Test one fixed causal rule only: if the latest available WTI close is above its 20-observation trailing close, take a next-day short exposure in the frozen V98 crypto training basket; otherwise stay flat. Macro observation must be lagged by one full day before crypto exposure. No sign flip, alternate lookback, threshold search, asset exclusion, or rescue is allowed after results are seen.

## Frozen scope
Training only: 2023-01-01 through 2025-12-31. Chronological annual folds: 2023, 2024, 2025. Validation and final holdout remain unopened and must not be read, scored, summarized, or used for selection.

Signal: DCOILWTICO[t] > DCOILWTICO[t-20], then short on crypto day t+1. Missing WTI observations are not imputed; carry-forward across missing publication days is forbidden for signal construction. Exposure gross target 30%, per-asset cap 35% of gross, equal-weight frozen training basket. No parameter fitting.

## Costs and stress
Apply the existing V98 Independent realistic trading-cost and funding model without reduction. Also report the same frozen severe and supersevere cost/funding stress multipliers used by recent V98 economic phases. No cost assumption may be changed after observing Phase150 output.

## Required diagnostics
For base, severe, and supersevere: total return, max drawdown, Profit Factor, payoff, win rate, positive days, turnover/trade count as applicable. Report each chronological fold separately. Report market-regime attribution, asset concentration, top positive/negative day tail concentration, and deterministic replay/hash/invariant checks.

## Frozen decision gates
Base aggregate return > 0; aggregate PF > 1.0; every annual fold return > 0 and PF > 1.0; severe aggregate return > 0 and PF > 1.0; supersevere aggregate return > 0 and PF > 1.0; max drawdown finite and reported; required diagnostics complete; deterministic replay identical; causality and holdout-firewall invariants pass. Failure of any gate => REJECT_NO_RESCUE. Passing all training gates permits only the next predeclared validation step; it does not authorize opening final holdout.

## Anti-overfit lock
Phase150 is one-shot. A failed sign, lookback, year, asset, regime, or cost case may be analyzed for mechanism but may not be repaired inside this family. Any later hypothesis must be scientifically distinct and separately preregistered before inspection.
