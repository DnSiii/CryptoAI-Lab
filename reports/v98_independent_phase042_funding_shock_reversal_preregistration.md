# V98 Independent Phase 042 — Funding Shock Reversal

## Status
PRE-REGISTERED after Phase041 rejection and before any Phase042 backtest result.

## Orthogonality rationale
Phase009 tested persistent funding *level* as carry. Phase042 does not retune that horizon or invert that failed signal: it tests a different mechanism, a change/surprise in positioning pressure. A sudden increase in recently paid funding relative to the contract's own trailing baseline may represent crowded long positioning vulnerable to relative reversal; a sudden decrease may represent crowded short positioning vulnerable to rebound.

## Frozen hypothesis and direction
Funding shock = 24h mean causal funding minus 168h mean causal funding. Frozen direction: long negative funding shock / short positive funding shock. No sign inversion after result.

## Frozen specification
- Point-in-time top-10 liquid universe; 720h liquidity history; 2160h minimum history.
- Funding panel shifted one hour before all rolling calculations; zero hours remain zero exactly as represented by the canonical point-in-time funding panel.
- Short funding pressure = 24h rolling mean, minimum 24 hourly observations.
- Baseline funding pressure = 168h rolling mean, minimum 168 hourly observations.
- Signal = negative(short mean - baseline mean), cross-sectionally ranked.
- Rolling BTC beta = 720h, minimum 360 observations, from lagged close-to-close returns.
- BTC excluded; score residualized against intercept + causal BTC beta.
- Rebalance every 24h; gross target/cap 0.75.
- Existing exact V98 costs/funding and severe/supersevere stresses unchanged.

## Gates and anti-overfit
Unchanged chronological folds, PF/DD, severe/supersevere PF/DD, concentration, tails/CVaR, payoff, win rate, positive days, turnover, beta neutrality and regimes. Validation opens only if training passes; final holdout remains untouched until training+validation pass and formal freeze. Exactly one direction, 24h/168h shock, 24h cadence and 0.75 gross; no sign/window/cadence/gross/threshold/regime search. Failure closes funding-shock reversal without rescue tuning.
