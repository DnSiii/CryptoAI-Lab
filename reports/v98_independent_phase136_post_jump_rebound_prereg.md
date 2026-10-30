# V98 Independent — Phase136 Post-Jump Rebound preregistration

Status: PREREGISTERED only after Phase135 PASS_DATA_ONLY. Phase134 remains REJECT_NO_RESCUE and is not retuned or rescued.

## Scientific question
Does the frozen Phase135 broad downside-jump event have positive next-day equal-weight expectancy that is stable across 2023/2024/2025 after realistic V98 costs/funding, rather than being an aggregate artifact?

## Frozen data/event definition
Use only V98 Independent canonical hourly data, 2023-01-01 through 2025-12-31 UTC, assets BTCUSDT/ETHUSDT/BNBUSDT/XRPUSDT/SOLUSDT. Reproduce Phase135 exactly: completed hourly log returns; per-asset scale = median absolute hourly log return over the preceding 28 completed UTC days; downside jump <= -3.0 * prior scale; broad event day requires jumps in >=3 assets. No alternate threshold, lookback, breadth, asset subset, timing, or event filtering.

## Frozen trade construction
At 00:00 UTC immediately after each completed event day, hold equal-weight long exposure across all five assets for exactly the subsequent completed UTC day, then flatten. Gross target = 0.50. No overlapping position stacking; if an event occurs while the one-day position is active, no extra gross is added. No parameter search or rescue.

## Costs and funding
Apply the repository's existing V98 Independent canonical base transaction-cost and realized funding accounting used by recent economic phases, plus the same frozen severe and supersevere friction multipliers. Report gross and net results separately. Gross exposure must never exceed 0.500000001.

## Frozen evaluation
Report aggregate and calendar-fold 2023/2024/2025: net return, max drawdown, Profit Factor, payoff, win rate, positive days, trade/event count; base/severe/supersevere costs; bull/bear/sideways regime attribution; asset contribution concentration; top-10 positive-day contribution; worst-day/tail statistics; deterministic hashes and exact rerun reproducibility.

## Frozen promotion gates
All must pass without retuning: aggregate base net return > 0; aggregate PF >= 1.05; each yearly fold net return > 0 and PF >= 1.02; severe aggregate net return > 0 and PF >= 1.02; supersevere aggregate net return > 0 and PF >= 1.00; max drawdown > -35%; no single asset contributes >45% of positive PnL; top-10 positive days contribute <35% of positive PnL; gross cap respected; deterministic rerun identical. Failure of any gate => REJECT_NO_RESCUE.

## Isolation
Validation and final holdout remain forbidden. No V16, V99, V99 workflows/reports/paper state, or Phase083 selection information. V98 Independent namespaced files only.