# V98 Independent — Phase235 pre-execution audit

Status: **AUDITED BEFORE PHASE235 RESULTS**.

Scope is limited to V98 Independent residual-skewness relative value. Holdout >=2026 remains forbidden; V16/V99 state is outside scope.

## Frozen hypothesis consistency
The evaluator implements the preregistered eight-spec family only: beta lookbacks 168/336h, residual-skew windows 72/168h, fixed k/horizon combinations exactly as frozen. Ranking direction remains long lowest residual skew and short highest residual skew. No result-conditioned sign flip, threshold, regime filter, universe edit, or rescue grid is permitted.

## Causality and accounting audit
- Hourly open-to-open returns are the primitive return series.
- Rolling BTC beta and residual skewness use trailing windows only.
- A decision at open(t) reads `signal.iloc[i-1]`, enforcing the t-1 information boundary.
- Portfolio construction is deterministic, equal-weighted long/short and normalized to gross <= 1.
- Funding is point-in-time, mapped to the next tradable hourly decision bucket and charged against lagged signed exposure.
- Turnover costs are frozen at 7/14/28 bp and must be monotone in the validator.

## Evaluation integrity
Calendar folds remain 2023, 2024, 2025 with a hard `<2026-01-01` firewall. Required diagnostics include total return, max drawdown, Profit Factor, payoff, win rate, positive-day fraction, trade tails, asset contribution/concentration, funding contribution, and lagged BTC bull/bear/sideways regimes.

## Reproducibility plan
Decision-grade execution must rebuild training-only canonical prices, verify price/funding chronology and firewall, assert the frozen source/grid/causality strings, run the evaluator twice, require byte-identical output, record SHA256, then run the independent mechanical gate. Any failure is a research failure or infrastructure issue to diagnose; it is not permission to tune.

## Gate
Use the preregistered annual gate unchanged: every base fold return > 0, PF > 1, positive days > 0.5, max DD > -50%; severe PF > 0.90 and supersevere PF > 0.80. Every fold must pass. Otherwise: **REJECT_FAMILY_NO_RESCUE**.
