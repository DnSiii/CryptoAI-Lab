# V98 Independent — Phase209 preregistration

## Hypothesis
**Cross-sectional dispersion-shock reversal.** When the four-alt cross-section experiences an unusually large one-hour dispersion shock, the most extreme relative winner and loser may partially mean-revert over the next few hours as temporary liquidity/positioning imbalances normalize. This is scientifically distinct from Phase208 volatility-compression breakout, Phase207 residual momentum, and Phase206 funding dislocation.

## Data firewall
- Branch: `research/v98-independent-zero` only; V98 Independent namespaced implementation/report files only.
- Assets traded: ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. BTCUSDT may be used only for the already-established causal regime diagnostic.
- Canonical 1h prices and frozen realized-funding snapshot, strictly `<2026-01-01`.
- Folds scored separately: calendar 2023, 2024, 2025. Pre-fold data is causal warm-up only.
- Validation/final holdout remains unopened and cannot influence code, parameters, selection, or promotion.

## Fixed causal signal
At decision hour `t`:
1. For each alt, compute the completed `t-1` open-to-open one-hour return. No data from bar `t` is used.
2. Compute cross-sectional dispersion `D(t-1)` as the population standard deviation of those four returns.
3. Compare `D(t-1)` with the causal empirical distribution of dispersion observations ending at `t-2`, over L calendar days, L in {30,90}.
4. A shock exists when `D(t-1)` is at or above percentile Q, Q in {0.90,0.975}.
5. On a shock, at `t` open go **short** the alt with the highest `t-1` return and **long** the alt with the lowest `t-1` return, equal absolute weights, market-neutral gross exposure. Ties resolve deterministically by asset symbol.
6. Hold exactly H hours open-to-open, H in {4,12}. No overlapping portfolio; ignore new shocks while a position is active.
7. No signal inversion, asset exclusion, stop, take-profit, regime filter, funding filter, or post-hoc rescue.

## Closed grid — exactly 8 specs
Cartesian product: L {30,90} × Q {0.90,0.975} × H {4,12}. No additional parameter search.

## Economics
Use the same frozen V98 Independent base/severe/supersevere execution-cost schedule and realized-funding accounting. Charge entry and exit turnover. Funding is aligned to the active position interval; missing funding events are not synthetically imputed. Preserve the existing V98 portfolio/equity convention.

## Required outputs per spec/fold/cost
Return, max drawdown, Profit Factor, payoff, win rate, positive-day fraction, trade count, best/worst full trade, p01/p05/p50/p95/p99 full-trade PnL tails, asset contribution/concentration, and bull/bear/sideways regime decomposition. Full-trade economics must include entry cost, holding price/funding PnL, and exit cost.

## Reproducibility/invariants
- Monotonic unique timestamps and strict `<2026-01-01` assertions for prices/funding.
- Scoring begins exactly at each fold start; warm-up cannot create a position entering the fold.
- Threshold reference distribution excludes `D(t-1)` itself.
- Exactly one winner and one loser are selected per accepted shock; portfolio net direction is zero at entry.
- Execute twice from frozen inputs and require identical deterministic result SHA256.

## Mechanical promotion discipline
A candidate cannot advance unless base-cost return is positive with PF > 1 in **all three** chronological folds, drawdown/tails/concentration are acceptable, and the aggregate edge is not explained by one asset or regime. Severe and supersevere economics must remain credible under the existing V98 governance gates. No gate is weakened here.

If the family fails, reject without rescue/tuning and move to a scientifically distinct hypothesis. Do not inspect validation/final holdout.
