# V98 Independent — Phase033 Beta Asymmetry preregistration

## Hypothesis
Cross-sectional **BTC beta asymmetry** may contain structural information beyond unconditional linear beta: assets that historically participate more in positive BTC hours than in negative BTC hours (upside beta minus downside beta) may exhibit better subsequent risk-adjusted relative returns. The signal uses only lagged observations and is neutralized to dollar and unconditional BTC beta.

## Frozen specification before results
- Universe: same V98 point-in-time liquid top 10 policy.
- Liquidity lookback: 720h; minimum history: 2160h.
- Inputs: closes shifted one hour before hourly return construction.
- Exposure window: 720h; minimum 180 observations in each BTC sign subset.
- At each rebalance estimate OLS beta separately on lagged BTC-positive and BTC-negative hourly observations for each eligible asset.
- Score: upside beta minus downside beta. Economic sign is frozen: long relatively high scores, short relatively low scores; no sign rescue.
- Cross-sectional construction: percentile-rank score minus 0.5, then regress that score on intercept and unconditional lagged BTC beta; residuals are portfolio weights.
- Rebalance: every 24h.
- Gross target/cap: 0.75.
- Costs/funding: canonical V98 base, severe and supersevere through exact_fast.
- Evaluation: canonical chronological training folds, max drawdown, PF, payoff, win rate/positive days, tails, concentration, beta neutrality and regime diagnostics.
- Gate discipline: validation opens only if frozen training gate passes. Final holdout remains untouched until a candidate is frozen after validation.

## Anti-overfit constraints
Single specification only. No search over sign, lookback, cadence, gross, thresholds, BTC-return cutoffs, regimes, winsorization, conditional definitions or transformations. If training fails, close beta-asymmetry without rescue and move to a genuinely different hypothesis. Never use V99 for selection or tuning.
