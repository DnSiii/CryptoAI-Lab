# V98 Independent — Phase225 exposure invariant audit

Date: 2026-10-03
Branch: `research/v98-independent-zero`
Scope: V98 Independent only

## Trigger
Decision-grade workflow run `37162638316` failed in the evaluator before producing an admissible Phase225 result.

## Finding
The failure is an implementation/invariant failure, not evidence for or against the preregistered abnormal-volume residual-reversal hypothesis. The evaluator assigns `1/N` weight independently to each event cohort. Because positions remain open for H bars and a new event cohort may start before the previous cohort exits, independently normalized cohorts can overlap. Aggregate gross exposure can therefore exceed the frozen `gross exposure <= 1` invariant. The run correctly stopped rather than silently clipping or accepting the result.

## Scientific disposition
- Phase225 alpha status: **NOT EVALUATED / NO DECISION-GRADE RESULT**.
- No parameter, threshold, horizon, cost assumption, fold, or gate may be changed in response to this failure.
- 2026+ remains closed.
- The fix must be mechanical only: portfolio construction must prevent overlapping cohorts from making total gross exposure exceed 1 while preserving the preregistered signal and event ranking.
- Any rerun must repeat deterministic dual execution, SHA comparison, 2023/2024/2025 folds, 7/14/28 bp costs, realized funding PIT accounting, regimes, tails, concentration, max drawdown, PF, payoff, win rate and positive-days checks.

## Required implementation fix
Use a deterministic capacity-aware allocator (or mathematically equivalent construction) that, at every entry timestamp, allocates only currently available gross capacity after accounting for still-open positions. It must not use future returns, later events, fold outcomes, or holdout information. If no capacity is available, the event is skipped mechanically. Existing positions must not be resized using future information.

This audit is intentionally recorded before any corrected Phase225 result is observed.