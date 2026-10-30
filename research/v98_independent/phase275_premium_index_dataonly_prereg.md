# V98 Independent Phase275 — Binance Premium Index Klines DATA_ONLY

Status: **PREREGISTERED / DATA_ONLY / ZERO ALPHA / ZERO PNL**.

## Independent information class

Phase275 tests the Binance USD-M **premium index** as a new V98 information family.

The premium index is distinct from the realized funding series used by frozen Phase252: funding is a discrete realized settlement cashflow, while premium-index klines represent the contemporaneous futures-vs-index premium input used by the exchange's funding mechanism. Phase275 does not assume predictive value; it only establishes whether this source is complete and reproducible enough for later research.

No prior V98 premiumIndexKlines family exists in the V98 namespace.

## Frozen source contract

Official Binance public-data archive family documented by `binance/binance-public-data`:

`https://data.binance.vision/data/futures/um/monthly/premiumIndexKlines/{SYMBOL}/1h/{SYMBOL}-1h-{YYYY}-{MM}.zip`

and the matching provider `.CHECKSUM` sidecar for every archive.

Frozen symbols:
- BTCUSDT
- ETHUSDT
- BNBUSDT
- SOLUSDT

Frozen period:
- 2023-01 through 2025-12 inclusive
- 36 monthly archives per asset
- 144 archives total
- 26,304 expected hourly timestamps per asset
- 105,216 expected asset-hours total

No daily-file fallback, alternate exchange, alternate symbol, mark-price/index-price substitution, missing-row fill, interpolation, or source shopping.

## DATA_ONLY integrity gates

PASS_DATA_ONLY requires:

1. all 144 exact monthly ZIP objects are available;
2. all 144 matching `.CHECKSUM` sidecars are available;
3. every ZIP SHA-256 matches its official sidecar;
4. each ZIP contains exactly one expected CSV member;
5. each monthly file has exactly the complete UTC 1h grid for that calendar month;
6. no duplicate or non-monotonic open timestamps;
7. all OHLC premium values finite;
8. kline geometry holds: high >= max(open,close), low <= min(open,close), high >= low;
9. each asset has exactly 26,304 unique hourly observations from 2023-01-01 00:00 UTC through 2025-12-31 23:00 UTC;
10. total asset-hours = 105,216;
11. normalized canonical CSV SHA-256 is recorded;
12. per-archive provider checksum and local SHA-256 are recorded;
13. two independent deterministic reconstructions from the verified local archive set produce byte-identical canonical CSV and integrity metadata;
14. no crypto return join;
15. no direction/threshold/window selection;
16. no parameter search;
17. no PnL/backtest;
18. no validation/holdout access;
19. no 2026+ source object;
20. V14/V15/V99 excluded.

Any mandatory failure => **FAIL_DATA_NO_ALPHA** and closes this exact premium-index source path without repair/substitution inside Phase275.

A PASS authorizes only a separately preregistered Phase276 economic hypothesis.

## Isolation

Branch `research/v98-independent-zero`, V98 Independent namespace only.
Phase083 remains permanently ineligible.
