# V99 R106 Phase136 — OKX Cross-Venue Hourly Data Feasibility Preregistration

Status: PREREGISTERED / DATA_ONLY / NO ALPHA / NO PNL

## Purpose

Phase135 closed the canonical Binance/OHLCV continuation path. Phase136 tests a genuinely new information source before any further V99 alpha is authorized: independent OKX USDT perpetual-market history that could later support cross-venue dislocation/lead-lag research.

This phase is source feasibility only. It must not compute Binance-vs-OKX spreads, returns, correlations, signals, alpha, trades or PnL.

## Source

Official OKX public market endpoint:
- GET https://www.okx.com/api/v5/market/history-candles
- bar = 1H
- public/no account credential

The endpoint documentation states that history-candles retrieves historical candlesticks from recent years and supports timestamp pagination.

## Frozen training window

- start inclusive: 2021-12-01T00:00:00Z
- end exclusive: 2024-01-18T00:00:00Z
- no timestamp at or after end may be admitted to the feasibility corpus.

## Frozen instruments

Exactly these five OKX USDT perpetuals:
- BTC-USDT-SWAP
- ETH-USDT-SWAP
- SOL-USDT-SWAP
- XRP-USDT-SWAP
- DOGE-USDT-SWAP

No post-result symbol substitution is allowed.

## DATA_ONLY firewall

The persisted report may contain:
- source identity;
- instrument IDs;
- row counts and expected hourly counts;
- coverage ratios;
- first/last timestamps;
- duplicate/gap/unfinished-candle counts;
- normalized payload hashes;
- retry/request counts;
- PASS/FAIL metadata.

It must not contain:
- OHLC or volume values;
- return statistics;
- cross-venue price differences;
- correlation;
- direction;
- signal thresholds;
- alpha/PnL/trade metrics;
- any V99 holdout market values.

## Feasibility gates

PASS only if:
1. all returned rows are confirmed completed candles;
2. timestamps are unique and strictly hourly after normalization;
3. no admitted timestamp is outside the frozen train window;
4. at least 4 of 5 frozen instruments have >=98% hourly coverage across the frozen window;
5. each of the four existing train-fold boundary regions is represented for each passing instrument;
6. two independent acquisitions produce identical normalized full-row SHA-256 for every passing instrument;
7. no V16 Frozen, V99 Frozen, paper state, validation or untouched-holdout data is modified or used.

If fewer than 4 instruments pass, Phase136 is FAIL_DATA_NO_ALPHA and the source is not admitted.

## Next-step contract

A Phase136 PASS permits only a separate, pre-registered cross-venue economic hypothesis. The direction, feature, lag, portfolio construction and gates must be frozen after this data-only result and before any cross-venue PnL is inspected.

A Phase136 FAIL closes OKX cross-venue hourly candles as the immediate V99 source path. No threshold relaxation or symbol substitution is allowed.
