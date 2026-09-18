# V99 R106 Phase61 — native taker-flow 24h continuation pre-registration

Status: PRE-REGISTERED BEFORE ALPHA EVALUATION.

Phase60 passed full PIT48 train-only native taker-buy coverage. Phase61 tests exactly one economic hypothesis: persistent aggressive-buying pressure predicts relative continuation.

- Source: Binance USD-M 1h native `taker_buy_quote_volume` and `quote_volume`; no OHLCV proxy.
- Raw pressure per completed hour: `2 * taker_buy_quote_volume / quote_volume - 1` (undefined when quote volume <= 0).
- Feature: simple trailing 24 completed-hour mean of raw pressure, then `shift(1)` before portfolio formation. No alternative horizon, smoothing, sign flip, threshold, winsorization, or grid.
- Direction: continuation only (higher lagged pressure -> long relative; lower -> short relative).
- Portfolio mapping: existing deterministic Phase31 cross-sectional `weights(feature, close)` and Phase47 evaluation machinery; alpha gross fixed at 0.20.
- Phase61A selection gate is TRAIN ONLY through frozen train_end. Temporal folds, severe costs, PF, robust-mean-without-top1%, active-hour requirements are unchanged from Phase47. No holdout feature values or returns may be parsed in Phase61A.
- A family exists only if this single fixed transform passes the train/fold gate. There is no family/horizon selection in Phase61A.
- Only after a Phase61A pass may a separate Phase61B inspect the frozen selected specification on untouched holdout; failure cannot trigger retuning.
- V16 Frozen and V99 Frozen are immutable.

This pre-registration intentionally prevents learning the sign/horizon from outcomes.
