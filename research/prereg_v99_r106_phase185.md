# V99 R106 Phase185 — BTC shock → ETH one-hour lead/lag continuation

Status: PREREGISTERED BEFORE PNL. TRAIN ONLY. NO HOLDOUT.

## Scientific hypothesis
A sufficiently unusual BTC hourly return can transmit to ETH with a one-hour delay. This is economically distinct from Phase183/184: it does not trade an ETH/BTC residual level or its reversal/continuation. It tests cross-asset lead/lag after an exogenous BTC shock.

## Frozen construction
- Canonical BTCUSDT/ETHUSDT 1h pair only; exact timestamp match required.
- TRAIN market values only: timestamps strictly before 2024-01-18T00:00:00Z. Loader must stop before parsing post-cutoff OHLCV values.
- Economic evaluation begins 2021-12-01T00:00:00Z after warm-up.
- At decision hour t, use only BTC returns ending at or before t-1.
- Rolling window: 168 completed hourly BTC returns.
- Shock score: z-score of the latest completed BTC return versus the same 168-return window.
- Entry: |z| >= 2.0 only.
- Direction: ETH continuation in the sign of the BTC shock.
- ETH gross exposure: 0.20; otherwise flat. No BTC leg.
- Position chosen at t earns ETH close(t)→close(t+1). No contemporaneous t return may enter the signal.
- No parameter/sign/window/threshold retuning after PnL observation.

## Frozen gates
1. Causality/integrity invariants before PnL.
2. Five chronological TRAIN folds.
3. Severe cost 7 bps per side and supersevere 14 bps per side on ETH turnover.
4. TRAIN alpha pass requires severe >=4/5 positive folds; supersevere >=3/5 positive folds; supersevere total return >0; supersevere remove-best-hour return >0.
5. If alpha passes, freeze candidate before regime matrix, benchmark envelope, tail/concentration audit. Holdout remains untouched until all downstream TRAIN gates pass.
6. If alpha fails, permanent rejection without retuning.

## Motivation from prior evidence without tuning
Phase183 and Phase184 rejected both signs of the same beta-residual dislocation family. Their paired failure indicates that merely reversing that residual signal is not a justified next search direction. Phase185 therefore changes the economic mechanism to directional cross-asset information transmission while preserving the same anti-overfit gates.
