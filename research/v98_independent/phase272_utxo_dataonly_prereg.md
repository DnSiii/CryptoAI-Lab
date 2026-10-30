# V98 Independent Phase272 — Bitcoin UTXO Set Size DATA_ONLY

Status: **PREREGISTERED / DATA_ONLY / ZERO ALPHA / ZERO PNL**.

## Independent information class

Phase272 tests the historical size of the Bitcoin UTXO set: the total number of valid unspent transaction outputs.

This is distinct from:
- address/transaction counts;
- fee burden;
- hashrate/network security;
- confirmed block size;
- mempool congestion;
- exchange/funding/OI/order-flow;
- developer activity;
- macro/CFTC data.

The underlying UTXO set is a deterministic state derived from confirmed blockchain history.

## Frozen source

Source: Blockchain.com Charts API.

Fixed endpoint:
`https://api.blockchain.info/charts/utxo-count?start=2023-01-01&timespan=3years&format=json&sampled=false`

No alternate chart/provider, address-count substitution, transaction-count substitution, smoothing, direction, threshold or economic rule inside Phase272.

## DATA_ONLY gates

Training only: 2023-01-01 through 2025-12-31 UTC.

PASS_DATA_ONLY requires:
1. >=95% normalized daily coverage;
2. zero duplicate normalized dates after deterministic same-day averaging;
3. every retained UTXO count finite and strictly >0;
4. no unexplained gap >3 days;
5. first date <=2023-01-03;
6. last date >=2025-12-29;
7. no observation outside training;
8. raw response SHA-256 recorded;
9. normalized CSV SHA-256 recorded;
10. two independent acquisitions byte-identical;
11. zero crypto-price/return join;
12. zero direction/threshold selection;
13. zero parameter search;
14. zero PnL/backtest;
15. validation/holdout untouched.

Failure => FAIL_DATA_NO_ALPHA.

A PASS only authorizes a separately preregistered economic hypothesis using completed prior-day observations. No module promotion.

## Isolation

V98-only branch/namespace. 2026+ forbidden. Phase083 selection use forbidden. V14/V15/V99 excluded.
