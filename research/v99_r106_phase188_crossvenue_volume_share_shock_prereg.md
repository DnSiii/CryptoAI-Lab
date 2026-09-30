# V99 R106 Phase188 — Cross-venue volume-share shock → relative continuation

Status: **PREREGISTERED / NO PNL INSPECTED**
Date: 2026-09-30

## Motivation
Orthogonal microstructure observable: where spot activity occurs across venues, rather than cross-venue price/return disagreement.

## Frozen construction
BTCUSDT + ETHUSDT spot, Binance + OKX hourly canonical sources. For symbol s and completed hour u:
`share_s,u = qvol_binance_s,u / (qvol_binance_s,u + qvol_okx_s,u)` using positive finite comparable quote/notional volume only.
`x_u = logit(clip(share_ETH,u,.01,.99)) - logit(clip(share_BTC,u,.01,.99))`.
At decision t, standardize x_(t-1) against fixed 168 completed observations ending t-2. Trigger |z|>=2.0. Continuation: z>=2 long ETH/short BTC; z<=-2 short ETH/long BTC. Gross 0.20 (+/-0.10), one next hourly bar. No sweep/retuning of window, threshold, direction, clipping, gross or holding period after PnL.

## TRAIN-only gate
Hard firewall before parsing holdout; 5 chronological folds; canonical severe/supersevere costs; deterministic byte-identical double run; t-1 mutation invariant for price and volume; cost monotonicity; active-hour/tail/remove-best-hour audit. Regime matrix only if basic gate survives; benchmark envelope only if regime gate survives.

## Kill criteria
Reject without retuning for severe TRAIN <=0, <3/5 positive severe folds, supersevere <=0, remove-best-hour <=0, leakage/timestamp/data-semantic/non-determinism failure, or single-fold/regime/pathological concentration.

## Data-integrity precondition
Execute only after independently verifying Binance and OKX hourly volume fields are semantically comparable enough for the defined share, preferably quote/notional volume. If canonical OKX does not expose a compatible field, close Phase188 without PnL; do not substitute base volume or fabricate conversion.

Final holdout remains untouched. V16 Frozen and V99 Frozen are read-only.
