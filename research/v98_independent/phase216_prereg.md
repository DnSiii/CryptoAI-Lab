# V98 Independent — Phase216 preregistration

## Hypothesis
A large idiosyncratic hourly altcoin return relative to contemporaneous BTC, when preceded by elevated short-horizon realized volatility, may partially mean-revert over the next few hours. This is scientifically distinct from Phase215 cross-sectional ranking: it trades each alt against a BTC-adjusted shock threshold rather than selecting strongest/weakest assets.

## Causality
For decision timestamp `t`, all features end at `t-1`. Define hourly residual shock for alt `a` as `r_a(t-1) - beta_a * r_BTC(t-1)`, where `beta_a` is estimated only from the trailing 168 completed hourly observations ending at `t-2`. Realized volatility is the standard deviation of residual returns over the trailing 24 completed hours ending at `t-2`. Entry is at `t`; no information from `t` or later may enter signal construction.

## Frozen universe / folds
- Alts: ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- BTCUSDT used only as causal market control / regime reference.
- Training folds evaluated separately: calendar 2023, 2024, 2025.
- Validation/final holdout remains unopened.

## Exactly 8 frozen specs
Cartesian product:
- standardized residual shock threshold `z`: 2.0, 3.0
- residual-volatility floor percentile, computed expanding/training-only from information available before `t`: 50%, 75%
- hold: 3h, 6h

Direction: fade the residual shock (positive shock -> short alt; negative shock -> long alt). At most one live position per asset; signals during an existing hold are ignored. Equal notional per eligible position; portfolio exposure normalized so simultaneous positions do not increase total gross risk above 1.0.

## Costs / funding
Use the same V98 Independent cost convention already frozen for recent phases: base 0.07%, severe 0.14%, supersevere 0.28% round-trip-equivalent implementation convention, applied consistently by the evaluator. Realized PIT funding must be charged/credited for each alt position at funding timestamps crossed by the hold. No future funding may enter the signal.

## Required outputs
For every spec × fold × cost stress: total return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, best/worst trade, p01/p05/p50/p95/p99 trade tails, asset attribution/concentration, funding contribution, and bull/bear/sideways regime decomposition using the existing causal V98 regime convention.

## Mechanical training gate
A spec is training-fold coherent only if base return > 0 and base PF > 1 independently in 2023, 2024, and 2025. Passing this minimal gate does not imply promotion; any survivor must immediately undergo cost-stress, tails/concentration/regime, invariant, and reproducibility audits before validation is considered.

## Anti-overfit rules
- Exactly these 8 specs; no threshold/lookback/hold additions after results.
- No inversion or rescue of a failed family.
- No regime filtering chosen after results.
- No V99 information for tuning/selection.
- No validation/final holdout access unless a preregistered training survivor clears the full audit chain.
- Two deterministic executions must be byte-identical before any decision.
