# V98 Independent Phase 040 — Residual Volatility Compression

## Status
PRE-REGISTERED before any Phase040 backtest result.

## Hypothesis
Cross-sectional *change* in idiosyncratic volatility may carry information distinct from low-volatility level: contracts whose BTC-residual volatility has compressed over the latest 24h relative to their own 168h residual-volatility baseline may exhibit more stable near-term relative performance than contracts undergoing volatility expansion. The frozen direction is long compression / short expansion.

## Frozen specification
- Point-in-time top-10 liquid universe; 720h liquidity history; 2160h minimum history.
- Returns are close-to-close and shifted through lagged close (`close.shift(1)`), so the newest signal return is known before the target position.
- Rolling BTC beta: 720h, minimum 360 observations. Residual return = asset return - beta * BTC return.
- Short residual volatility: 24h, minimum 18 observations.
- Baseline residual volatility: 168h, minimum 120 observations.
- Signal = negative log(short_vol / long_vol), cross-sectionally ranked at each rebalance. No sign inversion.
- Rebalance every 24h; BTC excluded; ranked score residualized against intercept + contemporaneously-known rolling BTC beta.
- Gross target/cap 0.75.
- Existing exact V98 base execution costs/funding and severe/supersevere stresses unchanged.

## Gates and diagnostics
Existing V98 training gate unchanged: chronological folds, PF/DD, severe/supersevere PF/DD, concentration. Record payoff, win rate, positive days, daily tails/CVaR, turnover, exposure, beta neutrality and regimes. Validation opens only after training passes. Final holdout remains untouched until training+validation pass and candidate is formally frozen.

## Anti-overfit
Exactly one sign, 24h/168h compression ratio, 24h rebalance, 0.75 gross. No search over windows, thresholds, sign, gross, regimes or clipping. Failure closes this hypothesis without rescue tuning.
