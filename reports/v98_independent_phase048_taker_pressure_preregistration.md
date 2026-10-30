# V98 Independent Phase048 — Taker Pressure Preregistration

Status: frozen before any Phase048 return result.

## Hypothesis

The Binance USD-M public metrics field `sum_taker_long_short_vol_ratio` measures aggressive taker-side futures flow and is economically distinct from candle quote-volume, trade count, average trade size, funding and open-interest growth. Cross-sectionally, contracts with stronger strictly lagged taker buy/sell pressure are hypothesized to underperform weaker-pressure peers over the next holding interval because one-sided aggressive flow proxies short-horizon crowded demand and adverse subsequent inventory normalization.

## Frozen signal

Use the same causally canonicalized hourly public metrics archive already integrity-audited for Phase047. At each decision, use only the most recent `sum_taker_long_short_vol_ratio` observation timestamped strictly before that decision. Define the raw score as the negative cross-sectional percentile rank of `log(sum_taker_long_short_vol_ratio[t-1])` minus 0.5. Values must be finite and strictly positive. There is no rolling window, smoothing, threshold, clipping search or price/volume interaction in the alpha score.

Universe remains the existing causal top-10 liquid V98 universe; BTCUSDT is excluded from alpha holdings. At each 24h rebalance, regress the cross-sectional score on intercept plus the existing causal 720h BTC beta and trade the residual. Gross target/cap = 0.75. Positions are held constant between rebalances.

## Data handling

Daily Binance archive rows are sorted deterministically by their exchange timestamp. For each UTC hour, select the last valid positive taker-ratio observation timestamped inside that hour. No interpolation, backfill from a later hour, price-dependent repair or alpha-dependent source choice is allowed. Missing hours remain unavailable. Training data are acquired/evaluated first; validation is not evaluated unless the frozen training gate passes. Final holdout remains inaccessible until training and validation pass and a candidate is formally frozen.

## Evaluation

Exactly the existing V98 protocol: chronological training folds; realistic funding and base transaction costs; severe and supersevere costs/funding; regime analysis; concentration/tails; max drawdown; Profit Factor; payoff; win rate; positive days; beta/dollar neutrality; reproducibility and causality invariants. Validation opens only after a training pass. Final holdout remains untouched otherwise.

## Anti-overfit restrictions

No sign inversion after failure, alternate taker-ratio window, smoothing, cadence search, gross/leverage search, thresholding, regime filtering, symbol-subset search, combination with Phase047 OI growth or other failed signals, or V99 evidence/state. If the frozen specification fails, Phase048 taker-pressure reversal is closed.
