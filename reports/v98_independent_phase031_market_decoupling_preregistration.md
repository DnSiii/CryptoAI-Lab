# V98 Independent — Phase031 Market Decoupling preregistration

## Hypothesis
Assets whose lagged hourly returns are persistently less explained by BTC (low rolling BTC R-squared / high idiosyncratic share) may contain more independent cross-sectional information than tightly market-coupled assets. A beta- and dollar-neutral portfolio long low-R2 assets and short high-R2 assets tests whether market decoupling itself carries a structural premium.

## Frozen specification before outcome inspection
- Point-in-time liquid universe: top 10, 720h liquidity lookback, 2160h minimum history.
- All signal inputs use close shifted by one hour.
- Estimate rolling 720h BTC beta and rolling 720h BTC R-squared, minimum 360 observations.
- Score = 0.5 - percentile rank(R2): positive for decoupled names, negative for highly BTC-coupled names.
- Rebalance every 24h.
- At each rebalance regress score cross-sectionally on intercept + contemporaneously-known rolling BTC beta and trade only the residual, enforcing dollar/beta neutrality.
- Gross target/cap 0.75.
- Exact existing V98 cost/funding model at base, severe and supersevere settings.
- No sign inversion, window/cadence/gross/threshold/regime search after seeing results.

## Decision discipline
Training and chronological folds only for research selection. Validation may be opened only if the unchanged V98 training gate passes. Final holdout remains untouched unless a candidate passes training and validation and is formally frozen. Evaluate PF, payoff, win rate, positive days, max drawdown, tails/concentration, regimes, beta neutrality and cost/funding stresses. Reject on gate failure without rescue tuning.

## Independence note
This is not beta stability (Phase023): Phase023 studied variability of beta itself. Phase031 studies the fraction of each asset's return variance explained by BTC, i.e. persistent market commonality/decoupling. It does not use V99 evidence or parameters.