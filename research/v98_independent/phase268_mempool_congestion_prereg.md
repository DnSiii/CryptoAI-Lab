# V98 Independent Phase268 — Bitcoin Mempool Congestion DATA_ONLY

Status: **PREREGISTERED / DATA_ONLY / ZERO ALPHA / ZERO PNL**.

## Independent information class

Phase268 tests whether historical Bitcoin mempool congestion can enter the V98 information frontier.

This family is distinct from:
- Phase258/259 network-security hashrate;
- Phase108/109 native fee burden;
- Phase057 address/transaction activity;
- exchange price/volume/funding/OI/order-flow families;
- developer activity;
- Wikimedia attention;
- CFTC positioning.

The metric is the aggregate byte size of valid Bitcoin transactions waiting for confirmation.

## Frozen source

Source: Blockchain.com Charts API.

Fixed endpoint:
`https://api.blockchain.info/charts/mempool-size?start=2023-01-01&timespan=3years&format=json&sampled=false`

No alternate chart, mempool-count substitution, fee metric, provider, rolling transformation, or source rescue is permitted inside Phase268.

## Frozen interval and DATA_ONLY gates

Training interval only: 2023-01-01 through 2025-12-31 UTC, expected 1,096 calendar days.

Normalize all source observations to UTC calendar date. If multiple source points occur on one UTC date, deterministically average them; this is a source-normalization rule, not an alpha transformation.

PASS_DATA_ONLY requires:
1. >=95% normalized daily coverage;
2. zero duplicate normalized dates after aggregation;
3. every retained mempool-size value finite and >=0;
4. no unexplained gap >3 calendar days;
5. first retained date <=2023-01-03;
6. last retained date >=2025-12-29;
7. no retained timestamp outside the training interval;
8. raw response SHA-256 recorded;
9. normalized CSV SHA-256 recorded;
10. two independent acquisitions in the same workflow produce byte-identical normalized CSV and manifest;
11. zero crypto-price/return join;
12. zero signal direction or threshold selection;
13. zero parameter search;
14. zero PnL/backtest;
15. validation/holdout untouched.

Failure => **FAIL_DATA_NO_ALPHA** and closes this exact source path without rescue.

## Future causality contract

Only if Phase268 passes may a separately preregistered later phase use congestion observations. Any future economic phase must use only completed prior UTC-day mempool data for decisions on day t.

Phase268 itself authorizes no sign, window, threshold, position, or module.

## Isolation

V98 Independent namespace and branch only.
Phase083 remains permanently ineligible.
2026+ forbidden.
V14/V15/V99 not used.
