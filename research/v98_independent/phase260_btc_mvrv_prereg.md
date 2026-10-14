# V98 Independent Phase260 — Bitcoin MVRV DATA_ONLY

Status: **PREREGISTERED / DATA_ONLY / ZERO ALPHA / ZERO PNL**.

## Independent information class

Phase260 tests the availability and integrity of Bitcoin Market-Value-to-Realised-Value (MVRV), an on-chain valuation-state series not previously tested in the V98 namespace.

This phase is independent of the still-running Phase259 economic test. It does not use Phase259 outcomes, price returns, PnL, validation, holdout or external-engine benchmarks.

## Frozen source

Source: Blockchain.com Charts & Statistics API.

Fixed endpoint:
`https://api.blockchain.info/charts/mvrv?start=2023-01-01&timespan=3years&format=json&sampled=false`

Only the returned timestamp/value series is admissible. No alternate provider/chart/query rescue inside Phase260.

## Frozen interval and integrity gates

Training interval: 2023-01-01 through 2025-12-31 UTC, 1,096 expected calendar days.

PASS_DATA_ONLY requires:
1. >=95% normalized daily coverage;
2. no duplicate normalized date;
3. every retained MVRV value finite and strictly >0;
4. no unexplained gap >3 days;
5. first retained date <=2023-01-03;
6. last retained date >=2025-12-29;
7. no observations outside training;
8. raw response SHA-256 recorded;
9. normalized CSV SHA-256 recorded;
10. two independent acquisitions byte-identical;
11. zero crypto price/return join;
12. zero direction/threshold selection;
13. zero parameter search;
14. zero PnL/backtest;
15. validation/holdout untouched.

Any failure => **FAIL_DATA_NO_ALPHA**.

A PASS authorizes only a later separately preregistered economic mechanism using completed prior-day MVRV.

V14/V15/V99 and Phase083 selection information remain excluded.
