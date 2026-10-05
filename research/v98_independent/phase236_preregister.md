# V98 Independent Phase236 — preregistration

Status: FROZEN BEFORE ANY PHASE236 RESULT.
Date: 2026-10-05.

## Scientific hypothesis
Cross-sectional **lagged idiosyncratic kurtosis / tail-shape relative value** may contain information distinct from Phase235 residual skewness: after removing BTC beta with strictly lagged beta, assets with unusually different residual tail-heaviness can exhibit short-horizon relative mean reversion. This is a new family, not a rescue/tuning of Phase235.

## Information firewall / causality
- Research namespace only: `research/v98_independent` plus its V98-only workflow.
- Training/evaluation data must end strictly before 2026-01-01 UTC. Holdout 2026+ remains unopened.
- At decision `open(t)`, every feature must be computable through `open(t-1)` only.
- Residual at hour `u` must use beta estimated only through `u-1`.
- Funding must be point-in-time and charged only when applicable.

## Frozen family/grid
Universe: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT; BTC is benchmark and may receive zero direct cross-sectional signal.

Exactly 8 specifications, Cartesian product:
- beta lookback: 168h, 336h
- residual-kurtosis lookback: 72h, 168h
- holding horizon: 4h, 8h
- k=1 fixed extreme per side

Residual tail score: rolling excess kurtosis of lagged BTC-beta residual returns. Direction is preregistered as **mean reversion of tail-heaviness extremes**: long highest residual-kurtosis asset and short lowest residual-kurtosis asset, dollar-neutral, gross <= 1.0. No sign flip/rescue after results.

## Chronological evaluation
Independent calendar folds: 2023, 2024, 2025. No random CV. A specification must satisfy the frozen annual gate in every fold; no averaging away a failed year and no post-result parameter rescue.

## Costs / diagnostics
Evaluate base 7 bp, severe 14 bp, supersevere 28 bp turnover costs, plus PIT funding. Report at minimum return, max drawdown, Profit Factor, payoff, win rate, positive days, turnover, funding contribution, asset concentration/contribution, hourly tails, best/worst day, and bull/bear/sideways regime diagnostics.

## Reproducibility / invariants
Run evaluator twice from independently rebuilt training-only inputs and require byte-identical deterministic payload / matching SHA256. Mechanically validate frozen grid, folds, firewall, causality markers, gross exposure, cost monotonicity, finite metrics and no 2026+ timestamps.

## Decision rule
No holdout access unless the complete preregistered training gate passes. If any required annual gate fails, decision is `REJECT_FAMILY_NO_RESCUE`. A pass only promotes the family to the next validation gate; it does not authorize weakening stresses or opening holdout automatically.
