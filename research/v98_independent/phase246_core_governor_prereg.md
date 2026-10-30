# V98 Independent Phase246 — Structural Beta Core + Crash Risk Governor

Status: PREREGISTERED BEFORE PHASE246 PNL.

## Architecture role
Phase246 is the first two-slot V98 architecture prototype:
- Growth Core primitive: structural long Clean-4 beta.
- Risk Governor prototype: causal crash-state replacement hedge.

It is not a parameter rescue of Phase245. Phase245 used 30d/120d trend/breadth to choose long/short/flat. Phase246 is long by default and invokes a separate drawdown/short-term-loss governor only during a predefined crash condition.

## Frozen data
Phase243 authenticated Clean-4 BTC/ETH/BNB/SOL only, Dec-2022 warmup through 2025-12, native funding. XRP quarantined. No 2026+, no V14/V15/V99.

## Frozen structural Growth Core
From the first 2023 open, target +0.25 BTC, +0.25 ETH, +0.25 BNB, +0.25 SOL (gross 1.0).

## Frozen crash governor
Build an equal-weight Clean-4 market log-return index from hourly closes.

At each 23:00 UTC close(t):
- trailing peak = maximum market-index level over the **previous 90 days / 2160h**, excluding the current close;
- current drawdown = index(t) / trailing_peak - 1;
- short-term confirmation = equal-weight market log return over the **last 7 days / 168h**, ending at t;
- CRASH state iff drawdown <= -20% AND 7d market return < 0;
- CRASH target replaces the long core with -0.25 in each asset (gross 1.0);
- otherwise target is the structural long core +0.25 each.
- before enough 90d history exists, remain structural long.

Decision at 23:00 close executes next 00:00 open. No flat state, leverage, pyramiding, vol target, alternate threshold/lookback, asset selection, sign flip, or post-result rescue.

The 20% drawdown is frozen as a conventional crash-scale loss threshold; 90d defines a local peak and 7d negative return confirms continuing downside. These are not selected from Phase246 PnL.

## Costs
Same V98 tiers: BASE 7bp with funding 1/1; SEVERE 12bp with 1.25/.75; SUPERSEVERE 20bp with 1.75/.50. Gross cap 1.0.

## Frozen comparator
Run the exact structural long Clean-4 core through the same backtester under all three cost/funding tiers.

## Architecture improvement gate
Phase246 becomes **CORE_GOVERNOR_ARCHITECTURE_CANDIDATE** only if:
1. BASE total return > passive BASE total return.
2. BASE CAGR > passive BASE CAGR.
3. BASE max drawdown is strictly better (less negative) than passive BASE max drawdown.
4. BASE daily PF >= passive BASE daily PF.
5. BASE worst day >= passive BASE worst day.
6. At least 2/3 calendar folds positive and worst fold > -25%.
7. SEVERE return > passive SEVERE return.
8. SUPERSEVERE return > passive SUPERSEVERE return.
9. No ruin.
10. Max open gross <=1.000000001.
11. Max asset contribution share <=70%.
12. Top-10 absolute daily-return concentration <=40%.

Failure => REJECT_CORE_GOVERNOR_NO_RESCUE for this exact 90d-peak / -20% / 7d-negative governor. Structural beta remains a diagnostic primitive, not a promoted complete V98.
