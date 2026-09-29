# V99 R106 — Phase178 insurance-fund stress DATA preregistration

Date: 2026-09-29
Status: preregistered before data harvesting and before any alpha/PnL.

## Orthogonal hypothesis class

Exchange insurance-fund balance changes are a direct observable of derivatives-system loss absorption / liquidation stress. This is economically distinct from price, funding, OI, trader ratios, taker flow, premium index, order-book depth and macro series.

First-party Binance evidence predating TRAIN states that the Futures Insurance Fund history is public and that its balance is updated daily at 00:00 UTC. Phase178 will test **data admissibility only** first; no direction, threshold, lookback or position rule is authorized by this document.

## Immutable data gate

Candidate TRAIN interval remains `[2021-12-01T00:00:00Z, 2024-01-18T00:00:00Z)` with a hard firewall at the endpoint. Required before alpha design:

- first-party historical series or immutable first-party archive covering the full interval;
- explicit timestamp/update semantics and timezone;
- deterministic raw SHA-256 and canonical output SHA-256;
- row count, min/max timestamps, duplicate/conflict checks;
- expected daily grid, missing-day map, longest gap, coverage by existing temporal fold;
- proof that values are market-wide rather than user/account-specific;
- no use of post-firewall observations, even for cleaning or normalization;
- additional project t-1 lag after availability timestamp.

## Anti-overfit / no-rescue rules

- No PnL inspection until the data gate passes.
- No tuning of lookback, balance-change threshold, sign, smoothing, stress definition or exposure from returns.
- No replacement with third-party reconstructed balances merely because first-party coverage is inconvenient.
- No shortening TRAIN or dropping failed folds.
- If historical point-in-time coverage cannot be proven, reject Phase178 at the data gate.

## If data passes

A separate alpha preregistration must be committed before returns are inspected and must preserve chronological train-only selection, temporal folds, severe/supersevere costs, regime matrix, benchmark envelope, concentration/tail audits, reproducibility and untouched holdout.

V16 Frozen and V99 Frozen untouched.