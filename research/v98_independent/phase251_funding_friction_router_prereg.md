# V98 Independent Phase251 — Funding Friction Router

Status: PREREGISTERED BEFORE PHASE251 PNL.

## Architecture role

Phase251 tests a cost-aware **Regime Router + Dynamic Allocator** around the structural Clean-4 Growth Core.

The always-on Phase250 allocator is rejected and remains rejected. Phase251 does not change its frozen candidate weights or funding lookback. It introduces a new architectural decision: only pay turnover for funding-efficient allocation when its estimated carrying-cost benefit exceeds the transaction cost required to enter and unwind it.

## Frozen inputs

- Structural core target: +0.25 each BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT.
- Funding-efficient candidate target: same Phase250 rule, 30%/30% in the two cheapest trailing-funding assets and 20%/20% in the two most expensive.
- Funding lookback: exactly 168 hours / 7 days.
- Decision time: 23:00 UTC, execution next 00:00 open.
- BASE execution cost used for the router economics: 7 bp per unit of L1 turnover.
- Gross remains exactly 1.00 and all weights remain long.

## Frozen router rule

At each 23:00 decision:

1. Sum each asset's realized funding rates over the previous 168 hours.
2. Divide by 7 to form a causal one-day funding-cost estimate for each asset.
3. Construct the frozen Phase250 candidate weights (30/30/20/20, ascending funding cost, stable symbol-order ties).
4. Estimate one-day funding savings:
   equal_weight_expected_cost - candidate_expected_cost.
5. Compute conservative round-trip turnover from the **current target** into the candidate and from the candidate back to equal weight:
   L1(current - candidate) + L1(candidate - equal_weight).
6. Break-even threshold = round_trip_L1 × 0.0007.
7. Router selects the candidate allocation only when estimated one-day funding savings > break-even threshold.
8. Otherwise target is the equal-weight structural core.
9. Re-evaluate once daily. No hysteresis or extra hold rule.

The threshold is not fitted to returns. It is mechanically derived from the actual BASE transaction-cost contract.

No alternate lookback, weights, cost multiple, forecast horizon, threshold, hold period, asset subset, price filter, momentum filter, regime filter or post-result rescue.

## Frozen data / execution

Phase243 authenticated Clean-4 only; native V98 funding; XRP quarantined.
Training only 2023-2025; no 2026+, validation, holdout, V14, V15 or V99.

Existing BASE/SEVERE/SUPERSEVERE backtest costs and funding stress multipliers remain unchanged. The routing signal itself always uses the frozen 7bp BASE break-even cost so positions are identical across stress tiers.

## Frozen comparator

Exact equal-weight structural Clean-4 core.

## Promotion gate

Phase251 becomes **FUNDING_FRICTION_ROUTER_CANDIDATE** only if all are true:

1. BASE return > core return by at least 3% relative.
2. BASE CAGR > core CAGR.
3. BASE daily PF >= core PF.
4. BASE max DD is not worse than core by more than 2 percentage points.
5. BASE realized funding drag < core funding drag.
6. Marginal calendar return positive in at least 2/3 folds.
7. No calendar fold underperforms core by more than 5 percentage points.
8. SEVERE return > core SEVERE return.
9. SUPERSEVERE return > core SUPERSEVERE return.
10. No ruin.
11. Max open gross <= 1.000000001.
12. Every active target is either exact equal weight or exact 30/30/20/20.
13. Max absolute asset PnL contribution share <=70%.
14. Top-10 absolute daily-return concentration <=45%.

Failure => REJECT_FUNDING_FRICTION_ROUTER_NO_RESCUE for this exact cost-derived router. No validation/holdout.
