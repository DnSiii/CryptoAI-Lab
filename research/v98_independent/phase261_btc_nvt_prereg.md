# V98 Independent Phase261 — Bitcoin NVT DATA_ONLY

Status: **PREREGISTERED / DATA_ONLY / ZERO ALPHA / ZERO PNL**.

## Independent information class

Phase261 tests Bitcoin Network-Value-to-Transactions (NVT), a valuation-versus-network-settlement series not previously present in the V98 namespace.

This is economically distinct from Phase258 hashrate:
- Phase258 measures network security / mining power.
- Phase261 measures network valuation relative to transaction value.

Phase261 is DATA_ONLY and does not depend on the outcome of the still-running Phase259 strategy.

## Frozen source

Source: Blockchain.com Charts & Statistics API.

Fixed endpoint:
`https://api.blockchain.info/charts/nvt?start=2023-01-01&timespan=3years&format=json&sampled=false`

No alternate provider, chart, range or endpoint rescue is allowed inside Phase261.

## Frozen integrity gates

Training interval: 2023-01-01 through 2025-12-31 UTC.

PASS_DATA_ONLY requires:
1. >=95% of 1,096 expected daily dates after deterministic normalization;
2. no duplicate normalized date;
3. every NVT value finite and strictly >0;
4. no gap >3 calendar days;
5. first date <=2023-01-03;
6. last date >=2025-12-29;
7. no observation outside training;
8. raw response SHA-256 recorded;
9. normalized CSV SHA-256 recorded;
10. two independent acquisitions byte-identical;
11. zero price/return join;
12. zero direction/threshold selection;
13. zero parameter search;
14. zero PnL/backtest;
15. validation/holdout untouched.

Any failure => **FAIL_DATA_NO_ALPHA**.

PASS_DATA_ONLY would authorize only a separately preregistered later economic hypothesis using completed prior-day NVT.

V14/V15/V99 and Phase083 selection information remain excluded.
