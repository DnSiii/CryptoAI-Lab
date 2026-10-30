# V98 Independent Phase250 — Funding-Efficiency Dynamic Allocator

Status: PREREGISTERED BEFORE PHASE250 PNL.

## Architecture role

Phase250 tests a second, scientifically distinct Dynamic Allocator on top of the Clean-4 structural Growth Core.

It is not a funding-carry alpha resurrection:
- no short positions;
- no funding sign trade;
- no standalone carry portfolio;
- no asset deletion;
- the structural long beta core remains fully invested at gross 1.00.

The hypothesis is narrower: reduce realized funding drag while preserving broad market participation.

## Frozen rule

At each 23:00 UTC decision:

1. Use only funding events already settled and available by that time.
2. For each Clean-4 asset, compute the sum of realized funding rates over the previous **168 hours / 7 days**.
3. Rank assets from cheapest funding drag to most expensive funding drag. Ties are resolved by fixed symbol order: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT.
4. Two cheapest assets receive target weight **0.30 each**.
5. Two most expensive assets receive target weight **0.20 each**.
6. Total gross remains exactly **1.00**, all weights remain long.
7. Decision after 23:00 executes next 00:00 open and persists until next daily decision.
8. December 2022 is warmup; 2023-2025 only is scored.

No alternate funding window, weight spread, rank count, rebalance hour, gross, sign flip, funding threshold, price filter, regime filter, or post-result rescue.

## Frozen data / execution

Authenticated Phase243 Clean-4 only:
BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT.
Native V98 Phase206 funding.
XRP quarantined.
No 2026+, validation, holdout, V14, V15 or V99.

Existing V98 base/severe/supersevere cost and funding multipliers are unchanged.
Open gross cap = 1.00.

## Frozen comparator

Exact equal-weight structural Clean-4 core (+0.25 each) under the same backtester and cost/funding tiers.

## Promotion gate

Phase250 becomes **FUNDING_EFFICIENCY_ALLOCATOR_CANDIDATE** only if all are true:

1. BASE return > equal-weight core return by at least 3% relative.
2. BASE CAGR > core CAGR.
3. BASE daily PF >= core PF.
4. BASE max DD is not worse than core by more than 2 percentage points.
5. BASE realized funding drag is lower than core funding drag.
6. Marginal calendar return positive in at least 2/3 folds.
7. No fold underperforms core by more than 5 percentage points.
8. SEVERE return > core SEVERE return.
9. SUPERSEVERE return > core SUPERSEVERE return.
10. No ruin.
11. Max open gross <= 1.000000001.
12. Target weights always in {0.20, 0.30} when active and sum to 1.00.
13. Max absolute asset PnL-contribution share <= 70%.
14. Top-10 absolute daily-return concentration <= 45%.

Failure => REJECT_FUNDING_EFFICIENCY_ALLOCATOR_NO_RESCUE for this exact 7d / 30-30-20-20 allocator. No validation/holdout.
