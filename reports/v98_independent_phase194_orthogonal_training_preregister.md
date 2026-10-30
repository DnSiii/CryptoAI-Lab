# V98 Independent — Phase194 orthogonal training preregistration

**Status: FROZEN BEFORE ECONOMIC RESULTS. TRAINING ONLY.**

Validation remains untouched. Final holdout remains closed. V16/V99 must not be used for selection, tuning, comparison, or rescue.

## Scientific hypothesis

Test a **cross-sectional abnormal-volume reversal** family using the canonical quote-volume field as a genuinely distinct information source from the price/funding families in Phases189–193.

Economic rationale: unusually intense traded notional combined with an extreme cross-sectional one-bar move may represent temporary liquidity pressure/exhaustion. The test asks whether, after the shock is fully observed, buying the relative loser and shorting the relative winner for a short fixed horizon produces a robust dollar-neutral reversal edge.

This is not a rescue of Phase189 dispersion reversal: entry requires an independently measured lagged quote-volume shock, uses a one-bar cross-sectional return shock rather than multi-hour dispersion state, and has a fully frozen small grid before results.

## Frozen training window and folds

- Economic training window: 2023-01-01 through 2025-12-31 UTC.
- Chronological folds: calendar 2023, 2024, 2025.
- No 2026 observation may enter features, thresholds, selection, ranking, gates, or reports.

## Frozen causal signal

For each asset and hour t, compute quote-volume ratio = quote_volume[t-1] / trailing median quote_volume over the preceding 30 days ending at t-2. Compute the completed one-hour return at t-1. All quantities are therefore known before the position for t becomes active.

At a decision hour, require at least three assets with valid history. Among assets whose quote-volume ratio exceeds the frozen shock threshold, identify the cross-sectional largest positive and largest negative completed one-hour return. Enter only when both sides exist and their absolute completed return exceeds the frozen move threshold. Long the negative-return asset and short the positive-return asset at equal 0.5 absolute weights. Hold for the frozen horizon, then return flat until the next qualifying event; overlapping events are not stacked.

## Frozen grid — exactly 8 specifications

Cartesian product:

- quote-volume shock threshold: {2.0x, 3.0x} trailing 30-day median
- absolute completed one-hour move threshold: {0.75%, 1.25%}
- hold horizon: {3h, 6h}

No other threshold, lookback, sign flip, weighting scheme, asset subset, stop, funding filter, regime filter, or post-result rescue is permitted.

## Required economics and diagnostics

Use canonical V98 realistic execution costs and actual funding cashflows. Evaluate base, severe, and supersevere assumptions. Report total return/CAGR, max drawdown, Profit Factor, payoff, win rate, positive/negative days, turnover, gross/net exposure, chronological folds, bull/bear/sideways regimes, concentration, top/bottom-10 tail shares, trade/activity count and ruin status.

## Frozen gates

A specification can advance only if all existing V98 training gates pass: positive base/severe/supersevere edge with PF > 1, acceptable drawdown, all three chronological folds positive with PF > 1, regime breadth, concentration/tail limits, sufficient activity, and risk/invariant checks. Aggregate strength cannot override a failed fold or stress gate.

If none pass: `REJECT_FAMILY_NO_RESCUE` and do not open validation. If one or more pass: select strictly by the existing V98 hierarchy, freeze one candidate, and only then preregister untouched validation separately.

## Reproducibility/invariants

Runner must execute twice and produce byte-identical JSON. Assert max canonical timestamp < 2026-01-01. Assert signal inputs are shifted so the execution hour's return/volume cannot enter its own decision. Report `training_only=true`, `validation=null`, `final_holdout=null`, `v16_used=false`, `v99_used=false`. Any invariant failure invalidates the run rather than weakening a gate.
