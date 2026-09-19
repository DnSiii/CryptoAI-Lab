# V98 Independent — Phase049 Positioning Divergence preregistration

Status: FROZEN BEFORE ANY PHASE049 RETURN IS COMPUTED.

## Independent mechanism
Phase049 tests participant-positioning divergence in USD-M futures. This is distinct from Phase048 aggressor taker flow, Phase047 open-interest growth, funding, candle volume, price action, beta, correlation, and residual families. The public metrics archive already passed the shared integrity gate and exposes both `sum_toptrader_long_short_ratio` and `count_long_short_ratio`.

Economic hypothesis: when top-trader position long/short ratio is high relative to the broad-account long/short ratio, informed/large positioning is relatively more bullish and the contract subsequently outperforms peers. This is a participant-composition hypothesis, not a flow-pressure or crowding inversion.

## Frozen signal and portfolio
At each timestamp use only the latest strictly lagged hourly observation. Define positioning divergence as `log(sum_toptrader_long_short_ratio) - log(count_long_short_ratio)`. Cross-sectionally rank this divergence and use the centered positive percentile rank: higher top-trader-vs-broad positioning receives higher alpha. No sign inversion is permitted after seeing results.

Portfolio construction is frozen to the existing V98 discipline: point-in-time liquid universe top 10, BTC excluded from alpha holdings, 24h rebalance, 720h BTC-beta estimate with minimum 360 observations, dollar + BTC-beta neutralization by cross-sectional residualization, gross target/cap 0.75, and no threshold/smoothing/window/cadence/gross/regime/symbol-subset search.

## Evaluation gates
Use training and chronological folds only for research decisions. Evaluate realistic base costs/funding plus severe and supersevere cost/funding stresses; max drawdown, Profit Factor, payoff, win rate, positive days, concentration/tails, regimes, beta/dollar neutrality, and reproducibility. Validation may be acquired/evaluated only if the frozen training gate passes. Final holdout remains untouched until training and validation both pass and the candidate is formally frozen.

## Anti-overfit constraints
No V99 evidence may influence selection. No Phase048/047 combination, sign rescue, alternate ratio definition, nearby window, smoothing, threshold, regime cherry-pick, symbol subset, cadence, or leverage rescue is allowed. If Phase049 fails, close this exact participant-divergence family and move to a genuinely different mechanism.
