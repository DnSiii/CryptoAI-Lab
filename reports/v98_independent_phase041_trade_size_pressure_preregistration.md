# V98 Independent Phase 041 — Trade-Size Pressure

## Status
PRE-REGISTERED after Phase040 rejection and before any Phase041 backtest result.

## Orthogonality rationale
The canonical kline panel contains hourly trade counts in addition to quote-volume. Prior V98 volume work used volume attention, signed-volume pressure, volume/price divergence, and price impact per quote-volume; none of those represents the scale of individual transactions. Phase041 therefore tests a microstructure participation mechanism: a persistent rise in average quote-value per trade may proxy a shift toward larger/informed participation rather than simply more activity.

## Frozen hypothesis and direction
Contracts whose causal average quote-value per trade has risen over the latest 24h relative to their own 168h baseline will outperform contracts whose average trade size has contracted. Frozen direction: long rising trade-size pressure / short falling trade-size pressure. No sign inversion after result.

## Frozen specification
- Point-in-time top-10 liquid universe; 720h liquidity history; 2160h minimum history.
- Hourly average trade size = lagged quote_volume / lagged trades; both shifted by one hour before use. Nonpositive trade counts are missing, never imputed from future data.
- Short participation scale = 24h rolling median average trade size, minimum 18 observations.
- Baseline participation scale = 168h rolling median average trade size, minimum 120 observations.
- Signal = log(short_scale / baseline_scale), cross-sectionally ranked at rebalance.
- Rolling BTC beta = 720h, minimum 360 observations, computed from lagged close-to-close returns.
- BTC excluded. Ranked score residualized against intercept + causal rolling BTC beta.
- Rebalance every 24h. Gross target/cap 0.75.
- Existing exact V98 base costs/funding plus severe and supersevere cost/funding stresses unchanged.

## Gates and diagnostics
Use unchanged V98 chronological training folds and training gate. Record total return/CAGR, max drawdown, worst/best day, p01/p05/CVaR, PF, payoff, win rate, positive/negative days, turnover, gross/net exposure, concentration, beta neutrality and regime diagnostics under base/severe/supersevere execution assumptions. Validation opens only if training passes. Final holdout remains untouched until training and validation pass and the candidate is formally frozen.

## Anti-overfit
Exactly one direction, 24h/168h median ratio, 24h rebalance and 0.75 gross. No search over sign, windows, aggregation, cadence, gross, thresholds, clipping or regimes. Failure closes this hypothesis without rescue tuning.
