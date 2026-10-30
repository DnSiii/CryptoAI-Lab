# V98 Independent Phase250 — pre-result funding-efficiency novelty audit

Status: PRE-RESULT / NO PHASE250 PNL INSPECTED.

## Distinction from rejected funding-alpha families

Prior V98 funding research included market-neutral/cross-sectional carry and funding-shock alpha families. Those experiments attempted to earn alpha from funding itself and were rejected where applicable.

Phase250 is different:
- it never shorts;
- it never takes a standalone funding position;
- it does not change total gross;
- it keeps all four Clean-4 assets continuously long;
- it only redistributes 10 percentage points of portfolio weight from the two highest trailing realized-funding assets to the two lowest;
- its objective is to reduce carrying-cost leakage while preserving broad structural beta.

## Frozen geometry

At each daily 23:00 UTC decision:
- trailing realized funding window = 168 hours;
- rank ascending funding sum;
- cheapest two = 30% each;
- most expensive two = 20% each;
- total gross = 100%;
- no leverage expansion, no asset deletion, no price or return input.

## Interpretation policy

A pass requires higher terminal wealth/CAGR, lower realized funding drag, severe/supersevere superiority, and chronological marginal robustness versus the exact equal-weight core.

A smoother or cheaper portfolio that compounds less cannot pass.

Failure closes the exact 7d / 30-30-20-20 allocator without changing the window, weights, rank count or rebalance clock.
