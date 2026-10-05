# V98 Independent Phase240 — preregistration

Status: frozen before any Phase240 performance result.

## Motivation / independence
Phases235-239 tested residual distribution shape or persistence and were rejected. Phase240 moves to a different mechanism: **cross-sectional recovery after an idiosyncratic shock**, not a rolling moment/persistence statistic. The hypothesis is that a large lagged idiosyncratic residual shock creates temporary relative dislocation; subsequent partial recovery can be ranked without using contemporaneous information.

## Hypothesis
At decision open(t), compute each asset's most recent fully observed idiosyncratic residual shock at t-1 relative to a lagged rolling residual scale. Rank the signed standardized shock cross-sectionally and test **reversal**: long the most negative shock, short the most positive shock. Direction is frozen ex ante; no sign flip/rescue after results.

## Causality / information set
For each asset/hour u, beta to BTC is estimated with a rolling window using returns only through u-1 (`beta.shift(1)` semantics). Residual(u)=asset_return(u)-beta_lagged(u)*BTC_return(u). Residual scale at u is rolling MAD of residual observations ending at u-1, multiplied by 1.4826 and floored at 1e-8. Shock z(u)=residual(u)/scale_lagged(u). Decision at open(t) uses only z(t-1); positions cannot depend on return/funding at t or later.

## Frozen grid
- beta lookback: {168, 336} hours
- residual-scale lookback: {72, 168} hours
- k: 1 long / 1 short
- holding H: {4, 8} hours
- exactly 8 specs: Cartesian 2x2x1x2

Portfolio: long lowest z(t-1), short highest z(t-1), equal absolute sleeve weights, gross <=1. If required inputs are unavailable/nonfinite, do not trade that decision. No asset removal, threshold tuning, regime gating, sign flip, or parameter rescue after results.

## Evaluation
Chronological untouched folds: calendar 2023, 2024, 2025. Holdout >=2026-01-01 remains unopened. Funding must be PIT and charged by held signed exposure. Frozen round-trip cost schedules: base 7 bp, severe 14 bp, supersevere 28 bp, using the same decision-grade accounting convention as prior V98 phases.

Report per spec/year/cost: return, max drawdown, Profit Factor, payoff, win rate, positive days, turnover L1, signal events, hourly PnL tails p01/p05/p50/p95/p99, best/worst day, asset PnL/funding contribution and concentration, and bear/bull/sideways diagnostics.

## Reproducibility / invariants
Rebuild training-only source independently; assert monotonic unique timestamps and strict firewall <2026. Evaluator must be deterministic and run twice with byte-identical output/SHA. Independent validator must assert exact 8-spec grid, folds, cost schedules, lagged beta/scale causality markers, gross <=1, no >=2026 observations, and complete diagnostic fields.

## Decision discipline
Apply the unchanged V98 annual gate mechanically to every preregistered spec. A failed family is `REJECT_FAMILY_NO_RESCUE`. Any passing candidate proceeds directly to severe/supersevere, regime, concentration/tail and reproducibility gates before any holdout access. Holdout remains sealed unless all prior gates are satisfied.
