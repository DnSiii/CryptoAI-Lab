# V98 Independent Phase239 — preregistration

Status: frozen before any Phase239 performance result.

## Hypothesis
Test an orthogonal temporal-distribution feature: **lagged idiosyncratic residual sign persistence**. This is distinct from Phase238 linear residual autocorrelation: it discards residual magnitude and measures whether positive/negative residual signs persist more than expected. Economic hypothesis: assets with stronger idiosyncratic sign persistence may continue relative moves over a short holding horizon.

## Information set / causality
For each asset and hour u, estimate rolling beta to BTC using only returns available through u-1. Residual at u = asset return(u) - beta_lagged(u) * BTC return(u). Convert residual to sign {-1,0,+1}. At decision open(t), persistence statistic uses only sign observations through t-1. Position decided at open(t), never using return/funding from t or later.

## Frozen grid
- beta lookback: {168, 336} hours
- sign-persistence lookback: {72, 168} hours
- k: 1 long / 1 short
- holding H: {4, 8} hours
- exactly 8 specs: Cartesian 2x2x1x2

Statistic: mean over the persistence window of `sign(resid[u]) * sign(resid[u-1])`, using only pairs whose newest observation <= t-1. Rank cross-sectionally at each eligible decision. Long highest persistence, short lowest persistence, equal absolute sleeve weights, portfolio gross <= 1. No sign flip is permitted after results.

## Evaluation
Chronological untouched folds: calendar 2023, 2024, 2025. Holdout >=2026-01-01 remains unopened. Funding must be PIT and charged according to held signed exposure. Round-trip cost schedules remain frozen at base 7 bp, severe 14 bp, supersevere 28 bp with the same accounting convention as prior decision-grade V98 phases.

Report per spec/year/cost: return, max drawdown, Profit Factor, payoff, win rate, positive days, turnover L1, signal events, hourly PnL tails p01/p05/p50/p95/p99, best/worst day, asset PnL/funding contribution and concentration, and bear/bull/sideways diagnostics.

## Reproducibility / gates
Rebuild training-only source independently; assert monotonic unique timestamps and firewall <2026. Run evaluator twice and require byte-identical outputs/SHA. Independent validator must assert exact grid, folds, cost schedules, causality markers and gross constraint.

Annual gate is unchanged from the current V98 decision-grade protocol and must be applied mechanically to every preregistered spec without parameter, asset, sign, or regime rescue. A failed family is rejected and closed; a passing candidate proceeds directly to the next validation/stress gate before any holdout access.
