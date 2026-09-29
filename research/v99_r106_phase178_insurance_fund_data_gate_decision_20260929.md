# V99 R106 — Phase178 insurance-fund stress DATA gate decision

Date: 2026-09-29
Decision: REJECT at DATA gate; no alpha/PnL inspected.

## Evidence audited

First-party Binance material predating TRAIN establishes that the Futures Insurance Fund existed, that historical changes were exposed through an Insurance Fund History surface, and that the displayed balance was updated daily at 00:00 UTC. Binance also documents the economic mechanism: insurance funds absorb losses from bankrupt liquidations and may receive profits from positions taken over after bankruptcy.

However, the currently documented Binance developer API catalog does not expose a supported historical insurance-fund endpoint with a contract that proves immutable point-in-time retrieval for the complete project TRAIN interval `[2021-12-01T00:00:00Z, 2024-01-18T00:00:00Z)`. The current support surface is not sufficient evidence that today's downloadable history is an immutable archive of exactly what was observable at each historical timestamp.

## Failure mechanism / causal audit

A balance change is not a pure liquidation-stress observation. Binance can contribute assets, rebalance assets among insurance funds, and deploy excess assets for other purposes. Therefore `delta(balance)` confounds bankrupt-liquidation absorption with administrative transfers unless contemporaneous transfer provenance is available. Treating every negative delta as liquidation loss would be a semantic error even if the numeric history were complete.

Daily 00:00 UTC publication also means a value stamped on day D cannot be consumed by the strategy before its documented availability. Project t-1 would add another lag; no same-day rescue is permitted.

## Gate result

FAIL-CLOSED for Phase178 because both conditions below are unresolved:

1. immutable first-party full-TRAIN historical retrieval is not proven under a supported API/archive contract;
2. balance deltas cannot be uniquely attributed to liquidation stress because Binance documents discretionary contributions/rebalancing/deployment.

No third-party reconstruction, shortened TRAIN, inferred missing days, return-conditioned cleaning, or PnL inspection is authorized. This is a scientific rejection of this Binance data realization, not evidence that the economic hypothesis is false.

V16 Frozen, V99 Frozen and holdout remain untouched.
