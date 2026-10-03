# V98 Independent — Phase219 implementation audit

## Scope
Independent pre-result audit of the frozen Phase219 funding-extreme post-settlement mean-reversion implementation. No V16/V99 evidence or state was consulted for strategy selection.

## Preregistration fidelity
- Exactly 8 specs: lookback 90/270 funding observations × |z| 1.5/2.0 × hold 4h/8h.
- Signal direction is frozen contrarian: positive extreme -> short; negative extreme -> long.
- ETH/BNB/XRP/SOL only; no BTC trading leg.
- Calendar folds remain 2023, 2024, 2025 and data firewall is strictly before 2026-01-01.

## Causality
Funding z-score is computed on actual settlement observations. A settlement rounded to its containing hour is not eligible until one additional hour has elapsed, enforcing `fundingTime <= t-1h`. Positions start at decision hour `t`; hourly open-to-open PnL is applied with lagged position. Price changes explicitly use `pct_change(fill_method=None)`. Missing pre-warmup z-scores cannot create a signal.

## Exposure / execution
Per-asset holds do not overlap themselves. Simultaneous assets are normalized to total gross exposure <= 1. Turnover is charged at each position transition with frozen base/severe/supersevere cost schedules. Realized PIT funding is charged by lagged position sign at settlement hours; no favorable-funding filter exists.

## Diagnostics / invariants
Each spec × fold × stress emits return, MDD, PF, payoff, win rate, positive-day share, trades, p01/p05/p50/p95/p99 tails, best/worst trade, asset returns, max asset concentration, funding contribution and bull/bear/sideways diagnostics. Workflow runs the evaluator twice and requires byte-identical output, verifies monotonic cost stress, and applies the preregistered three-fold gate mechanically.

## Holdout / anti-overfit
Validation/final holdout remains unopened. Zero coherent training specs means family rejection with no inversion, asset/regime rescue, threshold extension or nearby search. This audit was written before harvesting Phase219 results.
