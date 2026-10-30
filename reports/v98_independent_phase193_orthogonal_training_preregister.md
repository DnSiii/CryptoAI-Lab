# V98 Independent — Phase193 orthogonal training preregistration

**Status: FROZEN BEFORE ECONOMIC RESULTS. TRAINING ONLY.**

Validation remains untouched. Final holdout remains closed. V16/V99 must not be used for selection, tuning, comparison, or rescue.

## Scientific hypothesis

Test a **cross-sectional funding-carry** family, orthogonal to Phase189 dispersion reversal, Phase190 volatility-shock continuation, Phase191 low-vol trend, and Phase192 residual momentum.

Economic rationale: perpetual funding is a directly observable transfer between longs and shorts. Persistent extreme positive funding may make the expensive long side unattractive and persistent negative funding may make the short side unattractive. The test asks whether a dollar-neutral portfolio that receives rather than pays cross-sectional funding has enough price-plus-funding edge to survive realistic execution costs.

This is not a price-momentum rescue. Selection uses lagged funding only; price returns are outcomes/risk, not ranking inputs.

## Frozen training window and folds

- Training economic window: 2023-01-01 through 2025-12-31 UTC.
- Chronological folds: calendar 2023, 2024, 2025.
- No 2026 observation may enter feature construction, parameter selection, ranking, gates, or reports.

## Frozen signal

At each rebalance timestamp, for each asset compute trailing funding sum using only funding observations whose timestamp is <= the immediately preceding bar timestamp. Rank assets by this lagged trailing funding sum.

Portfolio direction: **long the asset with the lowest trailing funding sum and short the asset with the highest trailing funding sum**, equal absolute weights, target gross 1.0 and target net 0.0. Positions become active only after the ranking timestamp. Funding cashflows must use the same position timing convention as the canonical V98 evaluator; no future funding may leak into ranking.

## Frozen grid — exactly 8 specifications

Cartesian product:

- funding lookback: {24h, 72h}
- rebalance/hold interval: {12h, 24h}
- funding extremeness gate: {none, cross-sectional spread >= trailing 30-day median spread}

Names: `f24_h12_g0`, `f24_h12_g50`, `f24_h24_g0`, `f24_h24_g50`, `f72_h12_g0`, `f72_h12_g50`, `f72_h24_g0`, `f72_h24_g50`.

For `g50`, the spread threshold at timestamp t must be computed only from cross-sectional funding spreads strictly available before t, with a 30-day trailing window. If history is insufficient, stay flat.

No other lookback, threshold, sign flip, weighting scheme, asset subset, stop, regime filter, or post-result rescue is permitted in Phase193.

## Required economics and diagnostics

Use canonical V98 realistic price execution costs and actual funding cashflows. Evaluate base, severe, and supersevere cost assumptions. Report total return/CAGR, max drawdown, Profit Factor, payoff, win rate, positive/negative days, turnover, gross/net exposure, chronological folds, bull/bear/sideways regimes, asset contribution/concentration, top/bottom-10 tail shares and ruin status.

## Frozen gates

A specification can advance only if all preregistered V98 training gates pass, including positive/credible edge under base and both stress levels, acceptable drawdown, chronological fold consistency, regime breadth, concentration/tail limits and invariant checks. A superficially attractive aggregate result cannot override a failed gate.

If none pass: `REJECT_FAMILY_NO_RESCUE` and do not open validation.

If one or more pass: select strictly by the pre-existing V98 gate hierarchy, freeze exactly one candidate, then proceed to the already-defined untouched validation protocol without retuning.

## Reproducibility/invariants

Runner must execute twice and produce byte-identical JSON. Assert max canonical timestamp < 2026-01-01. Report `training_only=true`, `validation=null`, `final_holdout=null`, `v16_used=false`, `v99_used=false`. Any invariant failure invalidates the run rather than weakening a gate.
