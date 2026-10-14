# V98 Independent Phase249 — Inverse-Vol Dynamic Allocator

Status: PREREGISTERED BEFORE PHASE249 PNL.

## Architecture role

Phase249 tests the **Dynamic Allocator** slot on top of the authenticated Clean-4 structural Growth Core. This is not an alpha sleeve and does not use momentum, residuals, funding, breakout state, macro regime, or any rejected family signal.

Comparator = structural Clean-4 equal-weight core:
+0.25 BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, gross 1.00.

## Frozen hypothesis

Reducing volatility drag through causal risk allocation can increase compounded wealth without lowering gross exposure.

At each 23:00 UTC close(t):

1. Compute hourly log returns for each Clean-4 asset.
2. Compute each asset's realized volatility over the previous **720 hours / 30 days**, including the return ending at close(t).
3. Raw allocation score = 1 / realized_volatility.
4. Normalize positive raw scores to gross 1.00.
5. Apply a hard **40% maximum target weight per asset** with deterministic redistribution of excess weight among uncapped assets proportional to their remaining inverse-vol scores.
6. All target weights remain long-only and sum to exactly 1.00 when the allocator is active.
7. Decision after 23:00 close(t) executes at next 00:00 open and persists to the next daily decision.
8. December 2022 is warmup; 2023-2025 only is scored.

No alternate vol lookback, cap, rebalance hour, gross, estimator, long/short sign, regime filter, asset subset, momentum filter, or post-result rescue.

## Frozen data / execution

Phase243 authenticated Clean-4 only:
BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT.
Native V98 funding.
XRP quarantined.
No 2026+, validation, holdout, V14, V15 or V99.

Existing V98 cost/funding tiers:
BASE 7bp; SEVERE 12bp; SUPERSEVERE 20bp with existing funding stress multipliers.
Open gross cap = 1.00.

## Frozen comparator

Exact equal-weight Clean-4 structural core in the same backtester and cost tiers.

## Dynamic Allocator promotion gate

Phase249 becomes **DYNAMIC_ALLOCATOR_CANDIDATE** only if all are true:

1. BASE combined return > equal-weight core return by at least 3% relative.
2. BASE CAGR > core CAGR.
3. BASE max DD is not worse than core by more than 2 percentage points.
4. BASE daily PF >= core PF.
5. Marginal calendar return positive in at least 2/3 folds.
6. No calendar fold underperforms core by more than 5 percentage points.
7. SEVERE return > core SEVERE return.
8. SUPERSEVERE return > core SUPERSEVERE return.
9. No ruin.
10. Max open gross <= 1.000000001.
11. Max target asset weight <= 0.400000001.
12. Max absolute asset PnL-contribution share <= 70%.
13. Top-10 absolute daily-return concentration <= 45%.

Failure => REJECT_DYNAMIC_ALLOCATOR_NO_RESCUE for this exact 30d inverse-vol / 40% cap allocator. No validation/holdout.
