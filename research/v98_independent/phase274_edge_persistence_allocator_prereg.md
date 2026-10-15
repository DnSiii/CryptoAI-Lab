# V98 Independent Phase274 — Opportunity Edge-Persistence Dynamic Allocator

Status: **PREREGISTERED BEFORE PHASE274 PNL**.

## Architecture role

Phase274 tests the missing **Dynamic Allocator** slot on top of the frozen Phase252 partial architecture.

It does not change the Phase252 funding signal, core weights, funding window, sign, or base opportunity size. The frozen Phase252 engine remains the floor.

Phase274 only decides whether to add a **second copy** of the already-frozen +0.25 Opportunity Sleeve when its own recent causal marginal contribution has been positive.

## Frozen causal allocator

Construct two BASE shadow portfolios using the same authenticated Clean-4 source and exact causal execution:
- CORE shadow: structural +0.25 BTC/ETH/BNB/SOL, gross 1.00.
- PHASE252 shadow: exact frozen core + carry-subsidized opportunity, gross 1.00/1.25.

At each 23:00 UTC decision after close(t):

1. compute relative shadow equity ratio R(t) = equity_Phase252(t) / equity_CORE(t);
2. compute trailing 720h / 30d marginal log return:
   edge30(t) = log(R(t) / R(t-720h));
3. BOOST is eligible iff:
   - the original frozen Phase252 opportunity signal is ON for the next interval; and
   - edge30(t) > 0.
4. If eligible, add one additional copy of the opportunity sleeve:
   +0.0625 BTC/ETH/BNB/SOL = +0.25 gross.
5. Otherwise integrated target remains exact Phase252.
6. Never reduce Phase252.
7. Maximum target gross = 1.50.
8. Decision after close(t) executes next open through the existing exact causal backtester.

The 30d marginal-performance window is frozen before PnL as a medium-horizon edge-persistence test.

No alternate lookback, threshold other than zero, scaling curve, hysteresis, stop, sign change, asset subset, source change or post-result rescue.

## Comparator

Exact Phase252 under identical data, execution, funding and BASE/SEVERE/SUPERSEVERE costs.

## Promotion gate

Phase274 becomes **EDGE_PERSISTENCE_ALLOCATOR_CANDIDATE** only if all are true:

1. BASE integrated return > Phase252 by >=5% relative;
2. BASE CAGR > Phase252 CAGR;
3. BASE daily PF >= Phase252 PF;
4. BASE max DD not worse by >5 percentage points;
5. BASE worst day >= -20%;
6. positive marginal return versus Phase252 in at least 2/3 calendar folds;
7. no fold underperforms Phase252 by >10 percentage points;
8. SEVERE return > Phase252 SEVERE;
9. SUPERSEVERE return > Phase252 SUPERSEVERE;
10. >=50 BOOST decision-days in training;
11. no ruin;
12. max open gross <=1.500000001;
13. max absolute asset contribution share <=70%;
14. top-10 absolute daily-return concentration <=45%.

Failure => **REJECT_EDGE_PERSISTENCE_ALLOCATOR_NO_RESCUE**.

No validation or holdout. V14/V15/V99 excluded.
