# V98 Phase252 Forward Paper Shadow — frozen start contract (2026-11-05)

Status: **FORWARD PAPER SHADOW ONLY — NOT LIVE — NOT MODEL SELECTION**.

## Purpose

The V98 final engine is not approved. This forward shadow exists so the user no longer has to wait for the entire research program before accumulating fresh real-world evidence.

The paper engine is the already-frozen, non-rejected Phase252 partial architecture only. Its forward results are quarantined from V98 research selection: they must never be used to tune windows, signs, thresholds, weights, assets, costs, or future V98 architecture choices.

## Frozen strategy

Clean-4:
- BTCUSDT
- ETHUSDT
- BNBUSDT
- SOLUSDT

Core:
- +0.25 target weight per asset continuously.

Opportunity:
- trailing 168h realized funding sum per asset;
- cross-asset mean of those four trailing sums;
- decision once daily after 23:00 UTC close;
- if mean <= 0, add +0.0625 per asset;
- otherwise sleeve flat;
- next target executes at next 00:00 UTC open;
- max target gross 1.25.

No parameter change, no rescue, no asset deletion, no leverage increase.

## Forward start

Paper epoch is **2026-11-05T20:00:00Z**. Historical data before that timestamp may be read only as warmup for the 168h funding signal. It is not counted as forward PnL.

Initial paper target at epoch is core-only (+0.25 each) until the first frozen 23:00 UTC decision.

## Data / execution contract

Only official Binance USD-M Futures public endpoints:
- /fapi/v1/klines for 1h OHLC;
- /fapi/v1/fundingRate for realized funding records and settlement markPrice.

No host/source fallback. HTTP 451/403/418 is a hard stop. Do not bypass jurisdiction/access restrictions.

Forward ledger:
- execute pending daily rebalance at 00:00 UTC open;
- 7 bp per side on absolute notional traded;
- signed realized funding applied at the official funding record markPrice;
- mark positions using completed 1h closes;
- no hidden leverage or borrowed cash;
- record NAV, drawdown, turnover, costs, funding and signal state.

## Isolation

- Paper results are observation only.
- Never feed them back into V98 training or candidate selection.
- No V14/V15/V99 signals or internals.
- No claim of V98 completion, superiority, live readiness or expected profit.
- Real-money execution remains forbidden until a complete V98 engine passes its own frozen training, separate validation, execution evidence and final approval gates.
