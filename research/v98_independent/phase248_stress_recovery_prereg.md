# V98 Independent Phase248 — Stress Convexity Sleeve

Status: PREREGISTERED BEFORE PHASE248 PNL.

## Architecture role

Growth Core primitive remains the authenticated Clean-4 structural beta core:
+0.25 BTCUSDT, ETHUSDT, BNBUSDT and SOLUSDT continuously, gross 1.00.

Phase248 adds a **Stress/Recovery Sleeve** whose purpose is to improve terminal wealth by reducing exposure only during broad, volatility-confirmed downside stress. It is not a rescue of Phase246:
- Phase246 used a 90-day peak drawdown plus 7-day confirmation and replaced the entire core with a full short state.
- Phase248 uses no peak drawdown, never flips net short, and only applies a temporary half-exposure overlay when independent breadth + volatility conditions coincide.

## Frozen hypothesis

At each 23:00 UTC close(t), using only data available through close(t):

1. For each Clean-4 asset, compute its 7-day / 168-hour close-to-close return.
2. Downside breadth is ON when at least **3 of 4** assets have 7-day return < 0.
3. Compute the equal-weight Clean-4 hourly log-return series.
4. Compute realized volatility as sqrt(sum of squared market hourly log returns over the last **24 hours**).
5. Compute a causal stress reference = **80th percentile** of the previous **720 hourly** RV24 observations, excluding the current RV24 observation.
6. Volatility shock is ON when current RV24 > the causal 30-day q80 reference.
7. Stress Sleeve ON iff downside breadth AND volatility shock are both ON.
8. When ON, sleeve target = **-0.125 per asset** for all four assets.
9. When OFF, sleeve target = zero.
10. Core stays +0.25 per asset at all times.
11. Combined target is therefore +0.125 per asset / gross 0.50 during stress, and +0.25 per asset / gross 1.00 otherwise.
12. Decision after the 23:00 close executes at the next 00:00 open and persists until the next daily decision.

No alternate percentile, breadth threshold, return lookback, vol lookback, sleeve weight, hold period, asset subset, sign flip, short-net state, stop, or post-result rescue.

## Frozen data / execution

Only authenticated Phase243 Clean-4:
BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT.
December 2022 warmup through 2025-12 training.
Native V98 funding.
XRP remains quarantined.
No 2026+, validation, holdout, V14, V15 or V99.

Existing V98 cost/funding tiers:
- BASE 7bp/side, funding debit/credit 1.00/1.00
- SEVERE 12bp/side, 1.25/0.75
- SUPERSEVERE 20bp/side, 1.75/0.50

Combined open-gross cap = 1.00.

## Frozen comparator

Exact structural Clean-4 core under the same backtester, costs, funding and training window.

## Stress/Recovery promotion gate

Phase248 becomes **STRESS_RECOVERY_SLEEVE_CANDIDATE** only if all are true:

1. BASE combined return > core BASE return.
2. BASE combined CAGR > core CAGR.
3. BASE max drawdown improves by at least **5 percentage points** versus core.
4. BASE daily PF >= core PF.
5. BASE worst day improves versus core.
6. Marginal combined-vs-core calendar return is positive in at least 2/3 folds.
7. No fold underperforms core by more than 5 percentage points.
8. SEVERE combined return > core SEVERE return.
9. SUPERSEVERE combined return > core SUPERSEVERE return.
10. No ruin.
11. Max open gross <= 1.000000001.
12. Max absolute asset contribution share <= 70%.
13. Top-10 absolute daily-return concentration <= 45%.

Failure => REJECT_STRESS_RECOVERY_NO_RESCUE for this exact breadth/volatility/half-exposure rule. No validation or holdout is opened.
