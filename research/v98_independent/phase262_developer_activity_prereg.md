# V98 Independent Phase262 — Ecosystem Developer Activity DATA_ONLY

Status: **PREREGISTERED / DATA_ONLY / ZERO ALPHA / ZERO PNL**.

## Independent information class

Phase262 tests public software-development activity as a new exogenous information family.

No prior V98 family uses GitHub commit activity of the four Clean-4 ecosystems. This is distinct from trading data, funding, on-chain usage, macro data, Wikipedia attention and Bitcoin hashrate.

## Frozen repository mapping

Chosen before commit-count retrieval:

- BTCUSDT -> `bitcoin/bitcoin`
- ETHUSDT -> `ethereum/go-ethereum`
- BNBUSDT -> `bnb-chain/bsc`
- SOLUSDT -> `anza-xyz/agave`

Repository existence/default branches and the presence of historical commits in January 2023 were verified before this preregistration. No repository may be substituted after data inspection.

## Frozen source / measurement

Source: GitHub REST API commit history for each fixed repository's default branch.

Training interval only: 2023-01-01 through 2025-12-31 UTC.

For each repo and each of the 36 calendar months:
- query commits with author/committer history constrained to that calendar-month UTC interval;
- paginate deterministically at 100 commits/page;
- count unique commit SHAs returned on the default branch;
- record first/last commit timestamp for that month;
- zero commits is an admissible observation, not missing data.

No issue count, PR count, stars, releases, contributors, code churn, language, branch selection or alternate developer metric may be inspected inside Phase262.

## Integrity gates

PASS_DATA_ONLY requires:

1. all 144 fixed repo-month acquisitions succeed;
2. exactly 36 normalized month rows per asset;
3. no duplicate asset/month;
4. each commit count is integer >=0;
5. each asset has commits in at least 24/36 months;
6. each asset has at least 100 commits over the 36-month interval;
7. every retained commit timestamp is within the requested month/training boundary;
8. no 2026+ commit enters normalized data;
9. normalized CSV SHA-256 recorded;
10. deterministic response-page hash ledger recorded;
11. two independent acquisitions in one workflow produce byte-identical normalized CSV and manifest;
12. zero crypto price/return join;
13. zero signal direction/window/threshold selection;
14. zero parameter search;
15. zero PnL/backtest;
16. validation/holdout untouched.

Any failure => **FAIL_DATA_NO_ALPHA**.

## Causality contract

If Phase262 passes, a future separately preregistered economic phase may use only **fully completed prior calendar months** at the time of a trading decision.

Phase262 itself computes no trading signal.

## Isolation

Only V98 Independent files/branch.
Phase083 selection use forbidden.
V14/V15/V99 not used.
