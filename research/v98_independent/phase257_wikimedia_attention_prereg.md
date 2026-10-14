# V98 Independent Phase257 — Wikimedia Public Attention DATA_ONLY

Status: **PREREGISTERED / DATA_ONLY / ZERO ALPHA / ZERO PNL**.

## Independent information class

Phase257 tests whether reproducible public-attention data from Wikimedia can be added to the V98 information frontier.

This is distinct from Phase011 quote-volume "attention": Phase011 measured internal trading volume. Phase257 uses exogenous human readership of public encyclopedia pages and does not read any crypto price, return, PnL, V14/V15/V99 or validation/holdout information.

## Frozen source

Source: Wikimedia Pageviews REST API, per-article daily pageviews.

Fixed endpoint family:
`https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/user/{article}/daily/{start}/{end}`

Fixed project/access/agent/granularity:
- project = en.wikipedia.org
- access = all-access
- agent = user
- granularity = daily

Requests are split mechanically by calendar year 2023, 2024, 2025. No provider/source fallback or title search is allowed inside Phase257.

## Frozen asset-to-article mapping

Chosen before pageview retrieval:

- BTCUSDT -> `Bitcoin`
- ETHUSDT -> `Ethereum`
- BNBUSDT -> `BNB_Smart_Chain_(blockchain_platform)`
- SOLUSDT -> `Solana_(blockchain_platform)`

BNB uses the unambiguous BNB Smart Chain ecosystem article rather than the `BNB` disambiguation page. No alternate article/title rescue is allowed after data inspection.

## Required interval and integrity gates

Training interval only: 2023-01-01 through 2025-12-31 UTC, expected 1,096 daily observations per asset.

PASS_DATA_ONLY requires all of:

1. each asset coverage >= 99.0%;
2. no duplicate asset/date row;
3. every retained pageview count is integer and >= 0;
4. no unexplained date gap > 3 days for any asset;
5. first retained date <= 2023-01-02 and last retained date >= 2025-12-30;
6. no retained observation outside 2023-01-01..2025-12-31;
7. all four fixed article mappings return observations;
8. normalized dataset SHA-256 is recorded;
9. each yearly response body SHA-256 is recorded;
10. deterministic rerun produces byte-identical normalized CSV and manifest;
11. zero crypto-price join;
12. zero alpha direction;
13. zero parameter search;
14. zero PnL/backtest;
15. validation/holdout remain untouched.

Any mandatory failure => **FAIL_DATA_NO_ALPHA**.

## Causality contract for any later phase

If and only if Phase257 passes, a later separately preregistered alpha phase may use pageviews known only through **t-1 completed UTC day** for a decision at day t. Phase257 itself computes no signal and authorizes no threshold/window selection.

## Isolation

Only V98 Independent namespaced files on branch `research/v98-independent-zero`.
Phase083 holdout remains permanently ineligible.
2026+ data forbidden.
V14/V15/V99 not used.
