# V98 Independent Phase045 — Quote-Liquidity Stability — Preregistration

Status: FROZEN BEFORE RESULT.

## Admission / overlap audit

Phase045 tests stability of dollar participation, not its level or direction. It is distinct from Phase011 volume attention (short/long notional-volume level), Phase025 price impact per quote-volume, Phase038 signed-volume pressure, Phase039 volume-price divergence, Phase041 average trade size, and Phase043 transaction-count intensity. No Phase044 result beyond its formal rejection is used to tune Phase045; no V99, validation, or final-holdout evidence is used.

## Economic hypothesis

Assets with stable lagged quote-volume participation may have more durable liquidity provision and less episodic/speculative flow than assets whose dollar turnover is highly erratic. Frozen direction: long lower 168h coefficient of variation of lagged quote volume; short higher coefficient of variation, after dollar/BTC-beta neutralization.

## Frozen specification

- Universe: point-in-time top-10 liquid contracts; 720h liquidity lookback; 2160h minimum history.
- Information timing: `quote_volume.shift(1)` only for the alpha; lagged close prices for BTC beta.
- Liquidity-stability measure: 168h rolling standard deviation of lagged quote volume divided by its 168h rolling mean; minimum 120 observations.
- Score: negative log of positive coefficient of variation; no level ratio, signed volume, price-impact or trade-count term.
- Cross-section: percentile rank minus 0.5, then residualize on intercept and causal 720h BTC beta (minimum 360 observations).
- Rebalance: every 24 hours. Gross target/cap: 0.75. BTC excluded; dollar/BTC-beta neutralization preserved.
- Evaluation: unchanged chronological folds; base/severe/supersevere costs and funding; regimes; concentration/tails; max drawdown; PF; payoff; win rate; positive days; reproducibility.

## Anti-overfit / gates

No sign inversion, nearby-window search, cadence search, gross/leverage search, threshold search, regime cherry-picking, or combination with failed signals after result. Validation may open only if frozen training passes. Final holdout remains untouched until training and validation pass and the candidate is formally frozen. V99 evidence is excluded from selection.
