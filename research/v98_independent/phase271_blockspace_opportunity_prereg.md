# V98 Independent Phase271 — Confirmed Blockspace Demand Opportunity Sleeve

Status: **PREREGISTERED BEFORE PHASE270 VALUES / BEFORE ANY PHASE271 PNL**.

Execution is conditional on Phase270 == PASS_DATA_ONLY. If Phase270 fails, Phase271 is automatically void and must not run.

## Hypothesis

Sustained high utilization of confirmed Bitcoin blockspace is a direct, consensus-anchored demand signal: users are paying to consume scarce settlement capacity. A high-utilization regime may coincide with stronger crypto-wide demand and can justify temporary additional long exposure on top of the frozen V98 Phase252 architecture.

This is distinct from:
- hashrate/network security expansion;
- native fee burden;
- mempool congestion;
- transaction/address counts;
- exchange volume/funding/OI;
- developer activity.

## Frozen signal

Source: Phase270 normalized daily average confirmed block size.

Causality:
- decision once daily after 23:00 UTC;
- latest admissible observation is **D-1 completed UTC day**;
- compare D-1 block size to a rolling reference built only from **D-91 through D-2**.

Rule:
1. require 90 complete prior reference days;
2. compute the 75th percentile of D-91..D-2 average block size;
3. ON iff block_size(D-1) > prior-90d 75th percentile;
4. otherwise OFF;
5. ON adds +0.0625 BTC/ETH/BNB/SOL = +0.25 gross;
6. frozen Phase252 core + carry-subsidized opportunity remains unchanged underneath;
7. no stacking beyond this single +0.25 sleeve;
8. decision at 23:00 close executes next 00:00 open.

Frozen constants:
- reference = 90 completed days;
- threshold = prior-window 75th percentile;
- sleeve = +0.0625 per Clean-4 asset;
- max integrated target gross = 1.50;
- no grid, alternate quantile, alternate window, sign flip, asset subset, stop, regime combination or post-result rescue.

## Comparator

Exact frozen Phase252 architecture under identical authenticated Clean-4 prices, funding, execution and BASE/SEVERE/SUPERSEVERE costs.

## Promotion gate

Phase271 becomes **BLOCKSPACE_OPPORTUNITY_CANDIDATE** only if all are true:
1. BASE integrated return > Phase252 by >=3% relative;
2. BASE CAGR > Phase252 CAGR;
3. BASE daily PF >= Phase252 PF;
4. BASE max DD not worse than Phase252 by >5 percentage points;
5. BASE worst day >= -20%;
6. positive marginal return versus Phase252 in at least 2/3 calendar folds;
7. no fold underperforms Phase252 by >10 percentage points;
8. SEVERE return > Phase252 SEVERE;
9. SUPERSEVERE return > Phase252 SUPERSEVERE;
10. >=60 ON decision-days in training;
11. no ruin;
12. max open gross <=1.500000001;
13. max absolute asset contribution share <=70%;
14. top-10 absolute daily-return concentration <=45%.

Failure => **REJECT_BLOCKSPACE_OPPORTUNITY_NO_RESCUE** for this exact 90d/75th-percentile/+0.25 rule.

No validation or holdout access. V14/V15/V99 excluded.
