# V98 Independent Phase255 — Broad-Funding Opportunity Router

Status: PREREGISTERED BEFORE PHASE254 PNL.

## Architecture role

Phase255 tests the **Regime Router** slot on top of the frozen partial V98 engine.

Frozen baseline:
1. Growth Core primitive: structural Clean-4 beta, +0.25 each.
2. Phase252 frozen Opportunity Sleeve candidate: +0.0625 each when cross-asset mean trailing 168h funding sum <= 0.

Phase255 does not alter Phase252 parameters. It adds a separate eligibility router deciding whether the already-frozen Opportunity Sleeve is allowed to turn on.

## Economic hypothesis

A negative cross-asset mean can be driven by one extreme contract. Cheap financing should be more reliable when it is broad across the market rather than concentrated in one symbol.

## Frozen router rule

At each 23:00 UTC close(t):

1. Compute each asset's trailing realized funding sum over the previous **168 hours / 7 days**.
2. Phase252 mean condition remains mandatory: cross-asset mean trailing funding <= 0.
3. Breadth condition: at least **3 of 4** Clean-4 assets individually have trailing funding <= 0.
4. Opportunity Sleeve is eligible iff BOTH mean condition and breadth condition are true.
5. If eligible: add the exact frozen Phase252 +0.0625 per asset, combined gross 1.25.
6. Otherwise: keep only the structural core +0.25 per asset, gross 1.00.
7. Decision after 23:00 executes at next 00:00 open and persists to the next daily decision.

The 3-of-4 rule is a fixed broad-majority definition, not selected from Phase252 returns.

No alternate breadth count, funding window, sign threshold, sleeve size, gross, asset subset, price filter, volatility filter, hold rule or post-result rescue.

## Frozen data / execution

Authenticated Phase243 Clean-4 only:
BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT.
Native V98 funding.
XRP quarantined.
Training 2023-2025 only.
No 2026+, validation, holdout, V14, V15 or V99.

Existing BASE/SEVERE/SUPERSEVERE costs and funding stress multipliers unchanged.
Open-gross cap = 1.25.

## Frozen comparator

Exact Phase252 target under the same data/backtester/costs/funding.

## Regime Router promotion gate

Phase255 becomes **BROAD_FUNDING_ROUTER_CANDIDATE** only if all are true:

1. BASE routed return > Phase252 BASE return.
2. BASE routed CAGR > Phase252 CAGR.
3. BASE daily PF >= Phase252 PF.
4. BASE max DD improves by at least 2 percentage points versus Phase252.
5. BASE worst day is not worse than Phase252.
6. Marginal calendar return versus Phase252 positive in at least 2/3 folds.
7. No calendar fold underperforms Phase252 by more than 5 percentage points.
8. SEVERE routed return > Phase252 SEVERE return.
9. SUPERSEVERE routed return > Phase252 SUPERSEVERE return.
10. No ruin.
11. Max open gross <= 1.250000001.
12. Routed opportunity activity < Phase252 opportunity activity (router must actually filter states).
13. Max absolute asset PnL contribution share <=70%.
14. Top-10 absolute daily-return concentration <=45%.

Failure => REJECT_BROAD_FUNDING_ROUTER_NO_RESCUE for this exact mean<=0 + breadth>=3 rule. No validation/holdout.
