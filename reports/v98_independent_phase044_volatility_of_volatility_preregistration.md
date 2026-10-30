# V98 Independent Phase044 — Residual Volatility-of-Volatility Stability — Preregistration

Status: FROZEN BEFORE RESULT.

## Admission / overlap audit

Phase044 is admitted as a second-order risk-stability mechanism, not a rescue of residual low-volatility or Phase040 compression. Prior low-volatility families rank the level of residual volatility; Phase040 ranks the 24h/168h volatility level ratio. Phase044 instead measures how unstable the *24h realized residual-volatility process itself* has been over 168h, normalized by its own 168h median volatility level. No Phase040 result, validation result, final holdout, or V99 evidence is used to choose the sign or parameters.

## Economic hypothesis

After removing lagged BTC beta, assets with a more stable residual-risk process may earn better cross-sectional relative performance than assets experiencing erratic volatility-of-volatility, because unstable idiosyncratic risk can proxy fragile positioning, discontinuous liquidity, or unresolved information shocks. Frozen direction: long lower normalized residual volatility-of-volatility; short higher normalized residual volatility-of-volatility.

## Frozen specification

- Universe: point-in-time top-10 liquid contracts; 720h liquidity lookback; 2160h minimum history.
- Information timing: prices are shifted one hour before returns/beta/residuals are computed.
- BTC beta: causal 720h rolling beta, minimum 360 observations.
- Residual realized volatility: rolling 24h standard deviation, minimum 18 observations.
- Volatility-of-volatility: rolling 168h standard deviation of the 24h residual realized-volatility series, minimum 120 observations.
- Scale normalization: divide volatility-of-volatility by the 168h rolling median of 24h residual realized volatility; score is negative log of this positive ratio.
- Cross-section: percentile rank minus 0.5, then residualize on intercept and causal BTC beta.
- Rebalance: every 24 hours.
- Gross target/cap: 0.75. BTC excluded; dollar/BTC-beta neutralization preserved.
- Evaluation: unchanged chronological folds; base/severe/supersevere costs and funding; regimes; concentration/tails; max drawdown; PF; payoff; win rate; positive days; reproducibility.

## Anti-overfit / gates

No sign inversion, nearby-window search, cadence search, gross/leverage search, threshold search, regime cherry-picking, or combination with failed signals after observing the result. Validation may open only if the frozen training gate passes. Final holdout remains untouched until training and validation pass and the candidate is formally frozen. V99 evidence is excluded from V98 selection.
