# V98 Independent Phase 040 — Funding Dispersion

## Status
PRE-REGISTERED before any Phase040 result is observed.

## Independent hypothesis
Cross-sectional perpetual-futures funding dispersion may contain a direct carry premium: contracts with unusually negative causal funding are held long and contracts with unusually positive causal funding are held short. This is distinct from Phase009 by using a slow, standardized funding level rather than a generic carry sleeve, and it is not conditioned on any Phase039 outcome beyond the decision to abandon that rejected family.

## Frozen specification
- Universe: point-in-time top 10 liquid contracts; 720h liquidity lookback; minimum 2160h history.
- Funding input: funding-rate frame shifted by one hour before any signal construction.
- Signal: negative 168h rolling mean funding, standardized cross-sectionally by rank at each rebalance. No sign inversion after results.
- Minimum funding observations: 14 non-null observations within the rolling window.
- Rebalance: every 24h.
- Market controls: rolling 720h BTC beta, minimum 360 observations; residualize ranked funding score against intercept + BTC beta.
- Gross target/cap: 0.75; BTC excluded from tradable names.
- Execution: existing exact V98 engine with realistic base costs/funding and severe/supersevere cost/funding stresses.

## Frozen gates
Use existing V98 training gate unchanged: chronological folds, training PF/DD, severe/supersevere PF/DD and concentration requirements. Validation is inaccessible unless training passes. Final holdout remains untouched unless training and validation both pass and the candidate is frozen.

## Required diagnostics
Training/folds, max drawdown, PF, payoff, win rate, positive/negative days, daily tails/CVaR, turnover, gross/net exposure, concentration, beta neutrality, regime attribution, severe and supersevere stress.

## Anti-overfit commitments
One hypothesis, one sign, one 168h window, one 24h cadence, one gross target. No grid search, rescue inversion, threshold search, regime filter, parameter neighborhood or post-result modification. A failure closes Phase040 and requires a genuinely different Phase041 hypothesis.
