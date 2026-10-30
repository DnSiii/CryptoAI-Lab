# V98 Independent Phase046 — Peer-Correlation Crowding — Preregistration

Status: FROZEN BEFORE RESULT.

## Admission / overlap audit

Phase046 tests structural co-movement/crowding among altcoin residuals. It is not Phase006 consensus-residual level, Phase003 dispersion, Phase031 BTC market decoupling, or the beta families: the signal is a rolling correlation coefficient between each asset's BTC-residual return and a leave-one-out peer residual basket. It does not use the sign or magnitude of cumulative residual returns. No V99, validation, or final-holdout evidence is used.

## Economic hypothesis

Assets whose lagged BTC-residual returns are persistently less correlated with their peer residual basket may be less exposed to crowded common-altcoin positioning and may deliver better cross-sectional relative performance. Frozen direction: long lower peer correlation; short higher peer correlation.

## Frozen specification

- Universe: point-in-time top-10 liquid contracts; BTC excluded from alpha book.
- Information timing: close shifted one hour before returns, beta, residuals and correlations.
- BTC beta: rolling 720h, minimum 360 observations.
- Peer basket: equal-weight mean BTC-residual return of the other eligible non-BTC assets at each timestamp (leave-one-out).
- Signal: negative 168h rolling correlation with leave-one-out peer basket; minimum 120 observations.
- Cross-section: percentile rank minus 0.5, residualized on intercept and causal BTC beta.
- Rebalance 24h; gross target/cap 0.75; dollar/BTC-beta neutralization preserved.
- Evaluation: unchanged folds, base/severe/supersevere costs+funding, regimes, concentration/tails, max drawdown, PF, payoff, win rate, positive days and reproducibility.

## Anti-overfit / gates

No sign inversion, window/cadence/gross/threshold search, regime cherry-picking, or combination with failed signals. Validation only after frozen training pass; final holdout only after training+validation pass and formal freeze. V99 excluded.
