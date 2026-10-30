# V98 Independent Phase 030 — BTC Lead Response

## Hypothesis
A persistent cross-sectional difference in how liquid altcoin perpetuals respond to *lagged* BTC hourly returns may create a causal lead-response alpha: after a recent BTC displacement, assets with historically stronger next-hour response to BTC may continue to reflect that information differently from weak responders.

## Fixed specification before outcome inspection
- Point-in-time top-10 liquid universe; BTC excluded from tradable names.
- Minimum history 2160h; liquidity lookback 720h.
- All signal inputs use prices lagged one hour (`close.shift(1)`).
- Estimate each asset's 720h rolling covariance of its hourly return with BTC return lagged one additional hour, divided by lagged-BTC variance (lead-response coefficient), minimum 360 observations.
- Driver is BTC's fixed 24h cumulative lagged return.
- Cross-sectional raw score = lead-response coefficient × 24h BTC driver; percentile-rank and center.
- At each 24h rebalance, regress score cross-sectionally on intercept and contemporaneously-known 720h BTC beta; trade only the residual, enforcing dollar and BTC-beta neutrality.
- Gross target/cap 0.75. No sign, horizon, cadence, threshold, regime, universe, leverage, or parameter search after seeing results.
- Evaluate training + chronological folds first, with base/severe/supersevere costs and funding stress, concentration/tails, drawdown, PF, payoff, win rate, positive days, beta neutrality and regimes.
- Validation is opened only if the existing V98 training gate passes. Final holdout remains untouched even if validation passes; a passing candidate must be frozen before a separate one-shot final-holdout gate.

## Anti-overfit / independence rule
This is a new lead-lag response mechanism, not a rescue of rejected residual trend, residual quality, beta-stability, funding, volatility, seasonality, liquidity-efficiency or shock-recovery families. A failure closes this fixed lead-response specification; do not invert its sign or retune its horizons from the observed result.
