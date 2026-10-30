# V98 Independent — Phase039 Volume-Price Divergence preregistration

Status: FROZEN BEFORE RESULTS.

## Hypothesis
Cross-sectional divergence between causal 24h price return and causal 24h relative quote-volume change may identify exhausted versus confirmed moves. The frozen interpretation is **continuation quality**: rank assets by `24h return * log(1 + 24h mean relative quote volume)`, long higher scores and short lower scores after dollar/beta neutralization. This is distinct from Phase038 signed-volume pressure because magnitude of the multi-hour price move interacts with participation intensity rather than averaging hourly signed volume.

## Frozen specification
- Point-in-time top-10 liquid futures universe; 720h liquidity lookback; 2160h minimum history.
- All close and quote-volume inputs shifted by one hour before feature construction.
- Relative quote volume = lagged quote volume / causal 720h rolling median, min 360 observations, clipped [0,5].
- Price move = lagged-close 24h pct change.
- Participation = 24h mean relative quote volume, min 18 observations.
- Score = price move * log1p(participation). No sign inversion, thresholds, regime filters or parameter search after results.
- 720h BTC beta, min 360; cross-sectional rank then OLS residualization on intercept + beta.
- Rebalance every 24h; gross target/cap 0.75.
- Existing V98 base/severe/supersevere costs and asymmetric funding stress unchanged.
- Training and chronological folds first. Validation opens only if the frozen training gate passes. Final holdout remains untouched unless training+validation pass and candidate is formally frozen.

## Required evidence
Training/folds, severe/supersevere, regimes, concentration, tails, max drawdown, daily PF/payoff/win rate/positive days, beta neutrality and reproducibility/causality checks. A training rejection closes this exact specification without rescue tuning.
