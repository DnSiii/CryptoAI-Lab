# V98 Independent Phase270 — Bitcoin Confirmed Blockspace Utilization DATA_ONLY

Status: **PREREGISTERED / DATA_ONLY / ZERO ALPHA / ZERO PNL**.

## Independent information class

Phase270 tests confirmed Bitcoin blockspace utilization through average block size.

Unlike mempool state, confirmed block contents are committed to the Bitcoin blockchain and are historically reconstructible. The metric is therefore materially more suitable for strict causal research than a retrospective mempool snapshot.

This family is distinct from:
- hashrate/network security;
- fee burden;
- transaction/address counts;
- exchange price/volume/funding/OI;
- developer activity;
- CFTC positioning;
- mempool congestion.

## Frozen source

Primary source: Blockchain.com Charts API.

Fixed endpoint:
`https://api.blockchain.info/charts/avg-block-size?start=2023-01-01&timespan=3years&format=json&sampled=false`

Metric: average confirmed block size in MB over the published daily series.

No alternate chart, fee metric, transaction-count metric, provider, threshold, direction or economic transformation inside Phase270.

## DATA_ONLY gates

Training interval only: 2023-01-01 through 2025-12-31 UTC.

PASS_DATA_ONLY requires:
1. >=95% normalized daily coverage;
2. zero duplicate normalized dates after deterministic same-day averaging;
3. every retained value finite and strictly >0;
4. no unexplained gap >3 days;
5. first date <=2023-01-03;
6. last date >=2025-12-29;
7. no retained observation outside training;
8. raw response SHA-256 recorded;
9. normalized CSV SHA-256 recorded;
10. two independent acquisitions in one workflow byte-identical;
11. source interpretation limited to confirmed-block utilization, whose underlying block contents are immutable/reconstructible;
12. zero crypto-price join;
13. zero direction/threshold selection;
14. zero parameter search;
15. zero PnL/backtest;
16. validation/holdout untouched.

Failure => FAIL_DATA_NO_ALPHA.

A PASS only authorizes a separately preregistered economic hypothesis using completed prior-day observations. It does not promote a module.

## Isolation

V98-only branch/namespace. 2026+ forbidden. Phase083 selection use forbidden. V14/V15/V99 excluded.
