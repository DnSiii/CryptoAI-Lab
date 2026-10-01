# V98 Independent Phase200 — preregistration (2026-10-01)

Status: FROZEN BEFORE RESULTS. Scope: training-only; validation/final holdout forbidden.

## Why this is scientifically distinct
Phase199 funding-pressure mean reversion failed structurally. Phase200 does not invert or rescue Phase199. It tests an orthogonal OHLCV-only mechanism: time-series volatility compression followed by directional breakout. No funding signal, no cross-sectional quantile selection, and no use of V99 evidence.

## Data / causality
- Canonical V98 Independent 1h OHLCV only, symbols from `config/v98_independent_phase050_data.json`.
- Hard cutoff: timestamps < 2026-01-01 UTC. Validation/final holdout must never be loaded.
- Every feature used for a position at hour t is shifted by one completed bar (t-1).
- A symbol is eligible only with complete lookback history; missing/invalid bars produce zero position.

## Frozen hypothesis and grid
A breakout is tradable only when realized volatility was compressed relative to its own trailing history.

Closed 2x2x2 grid (8 specs):
- compression lookback: 72h, 168h;
- breakout lookback: 24h, 72h;
- holding/rebalance horizon: 8h, 24h.

Compression definition: trailing 24h realized vol at t-1 below its rolling median over the chosen compression lookback. Breakout: close(t-1) above prior rolling high => +1; below prior rolling low => -1; otherwise 0. Prior rolling high/low excludes the breakout bar by an additional shift. Position is carried for the frozen holding horizon, with overlapping signals collapsed to sign(sum active signals), then equal-weighted across active symbols with gross exposure <=1.

## Evaluation
Chronological training folds: 2023, 2024, 2025 plus pooled training. No fold reshuffling.

Costs: use the same V98 Independent realistic base/severe/supersevere fee+slippage schedule already frozen in the branch. Funding is charged using the canonical funding series when available; if absent, the evaluator must explicitly report that and may not silently assume favorable funding.

Required metrics: total return, max drawdown, Profit Factor, payoff, win rate, positive days, trade/activity count, turnover, gross/net exposure, regime results, tails, loss concentration, per-symbol concentration, per-fold results, and base/severe/supersevere stresses.

## Gates / anti-overfit
No parameter changes after results. No sign inversion, cherry-picking, rescue filters, or V99-guided selection. Zero-activity specs fail. A candidate can advance only if it is positive in every chronological fold under base costs, pooled PF >1.05, pooled MDD >-35%, positive-days >50%, no single symbol dominates profit/loss, bear regime is not catastrophically negative, severe remains positive, and supersevere does not show structural collapse. If no frozen spec clears the gates, reject the entire family.

## Reproducibility
Two independent executions from the same canonical inputs must produce byte-identical normalized JSON report hashes. Record input hashes, code commit, config, fold boundaries, and invariant checks. Holdout remains untouched unless a candidate is formally frozen after all training gates.