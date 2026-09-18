# V98 Independent — Phase032 Beta Convexity preregistration

## Hypothesis
Cross-sectional differences in **lagged nonlinear BTC exposure** may contain return information not captured by linear beta. Assets whose historical response has positive versus negative BTC-return convexity can be ranked using only information available before the decision timestamp; the resulting score is then dollar- and linear-beta-neutralized.

## Frozen specification before results
- Universe: same point-in-time liquid top 10 policy used by V98 Independent.
- Liquidity lookback: 720h; minimum history: 2160h.
- Inputs: close prices shifted by one hour before return construction.
- Exposure window: 720h; min periods: 360h.
- For each asset regress lagged hourly asset returns on intercept, lagged BTC return, and centered squared lagged BTC return. The coefficient on the centered squared BTC-return term is the convexity score.
- Cross-sectional score: percentile rank of the convexity coefficient minus 0.5; no sign rescue after seeing results.
- Neutralization: at each rebalance regress the score cross-sectionally on intercept and the contemporaneously estimated lagged linear BTC beta; use residuals as weights.
- Rebalance: every 24h.
- Gross target/cap: 0.75.
- Costs/funding: canonical V98 base, severe and supersevere settings through exact_fast.
- Evaluation: canonical chronological training folds, max drawdown, PF, payoff, win rate/positive days, tails, concentration, beta neutrality and regime diagnostics.
- Gate discipline: validation opens only if the frozen training gate passes. Final holdout remains untouched until a candidate is frozen after validation.

## Anti-overfit constraints
Single specification only. No search over sign, lookback, cadence, gross, thresholds, regimes, winsorization or nonlinear transformations. If training fails, close this family and move to a genuinely different hypothesis. Never use V99 for selection or tuning.
