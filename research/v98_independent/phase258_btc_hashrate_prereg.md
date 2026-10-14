# V98 Independent Phase258 — Bitcoin Network Hashrate DATA_ONLY

Status: **PREREGISTERED / DATA_ONLY / ZERO ALPHA / ZERO PNL**.

## Independent information class

Phase258 tests whether a reproducible Bitcoin network-security series can enter the V98 information frontier.

No prior V98 hashrate/network-security/mining-power family was found in the V98 namespace before this preregistration. This is distinct from price/volume/funding/OI/order-flow/on-chain activity/pageviews and from the rejected Coin Metrics active-address/transaction family.

## Frozen source

Source: Blockchain.com Charts & Statistics API.

Fixed endpoint:
`https://api.blockchain.info/charts/hash-rate?start=2023-01-01&timespan=3years&format=json&sampled=false`

Only the returned timestamp/value series for the Total Hash Rate chart is admissible. No alternate provider, chart name, rolling-average variant, query range or source rescue inside Phase258.

## Frozen interval and integrity gates

Training only: 2023-01-01 through 2025-12-31 UTC.

PASS_DATA_ONLY requires:

1. >=95% coverage of the 1,096 expected UTC calendar days after normalization to date;
2. no duplicate date after deterministic same-day aggregation;
3. every retained hashrate value finite and strictly > 0;
4. no unexplained date gap >3 days;
5. first retained date <=2023-01-03;
6. last retained date >=2025-12-29;
7. no retained observation outside the training interval;
8. raw response SHA-256 recorded;
9. normalized CSV SHA-256 recorded;
10. two independent acquisitions in one workflow produce byte-identical normalized CSV and manifest;
11. zero crypto-price/return join;
12. zero direction/threshold selection;
13. zero parameter search;
14. zero PnL/backtest;
15. validation/holdout untouched.

Any failure => **FAIL_DATA_NO_ALPHA**.

## Causality contract

If and only if Phase258 passes, a later separately preregistered economic phase may use only hashrate observations whose UTC date is fully completed before the trading decision. Phase258 itself computes no signal.

## Isolation

V98 Independent namespace and branch only.
2026+ forbidden.
Phase083 selection use forbidden.
V14/V15/V99 not used.
