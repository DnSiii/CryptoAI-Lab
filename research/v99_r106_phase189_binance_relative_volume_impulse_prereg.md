# V99 R106 Phase189 — Binance spot relative quote-volume impulse

Status: **PREREGISTERED / NO PNL INSPECTED**
Date: 2026-09-30

## Motivation
Test information-flow/activity without cross-venue market-type contamination. Use only homogeneous Binance spot BTCUSDT/ETHUSDT hourly bars and their native quote-volume fields. This is a data-semantic correction after Phase188 was closed before PnL, not a response to economic results.

## Frozen signal
For each completed hour u, `lv_s,u = log(quote_volume_s,u)` for positive finite quote volume. Define `x_u = lv_ETH,u - lv_BTC,u`. At decision t, score x_(t-1) against fixed 168 completed observations ending t-2: z=(x_(t-1)-mean)/std. Trigger |z|>=2.0. Continuation: z>=2 long ETH/short BTC; z<=-2 short ETH/long BTC. Gross 0.20 (+/-0.10), hold one next hourly bar. No parameter, sign, threshold, window, gross, or horizon sweep after PnL.

## Mandatory integrity before PnL
Verify the canonical Binance cache exposes a native quote/notional-volume field for both symbols with identical semantics and sufficient TRAIN coverage. If not, close Phase189 without PnL. Never reconstruct quote volume from close*base-volume.

## TRAIN-only gate
Hard pre-parse holdout firewall; strict t-1; 5 chronological folds; canonical severe/supersevere costs; deterministic byte-identical double run; mutation test proving t price/volume cannot alter exposure at t; cost monotonicity; active-hour and remove-best-hour tail audit. Require severe TRAIN >0, >=3/5 positive severe folds, supersevere >0 and remove-best-hour >0. If basic gate passes, continue in the same chain to regime matrix then benchmark envelope. Any failure permanently rejects without retuning.

Final holdout remains untouched. V16 Frozen and V99 Frozen are read-only.
