# V98 Independent Phase043 — Trade-Intensity Pressure — Preregistration

Status: FROZEN BEFORE RESULT.

## Economic hypothesis

Cross-sectional changes in transaction arrival intensity may proxy broad participation/information arrival independently of notional volume and average trade size. Assets whose lagged hourly trade counts are persistently elevated versus their own recent baseline are hypothesized to outperform assets with contracting transaction intensity after dollar/BTC-beta neutralization.

This is distinct from Phase011 volume attention (notional volume), Phase025 liquidity efficiency (price impact per quote-volume), Phase038 signed-volume pressure, Phase039 volume-price divergence, and Phase041 average quote-value per trade. Phase043 uses only the count of executed trades, not quote/base volume or trade size.

## Frozen specification

- Universe: point-in-time top-10 liquid contracts; 720h liquidity lookback; 2160h minimum history.
- Information timing: `trades.shift(1)` only; no contemporaneous/future trade counts.
- Signal: log ratio of 24h median lagged trade count to 168h median lagged trade count.
- Cross-section: percentile rank minus 0.5, then residualize on intercept and causal 720h BTC beta (minimum 360 observations).
- Rebalance: every 24 hours.
- Gross target/cap: 0.75.
- BTC excluded from alpha book; dollar and BTC-beta neutralization preserved.
- Evaluation: unchanged chronological training folds; base/severe/supersevere costs and funding; regimes; concentration/tails; max drawdown; PF; payoff; win rate; positive days; reproducibility.

## Anti-overfit / gates

No sign inversion, nearby-window search, cadence search, leverage/gross search, threshold search, regime cherry-picking, or combination with failed signals after observing the result. Validation may be opened only if the frozen training gate passes. Final holdout remains untouched until training and validation pass and the candidate is formally frozen. V99 evidence is excluded from selection.
