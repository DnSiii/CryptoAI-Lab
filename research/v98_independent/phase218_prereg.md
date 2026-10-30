# V98 Independent — Phase218 preregistration

## Hypothesis
A causal **realized-volatility term-structure state** may contain information not used by the failed direction/persistence families: when short-horizon realized volatility is unusually elevated relative to a slower baseline, subsequent returns may exhibit a volatility-conditioned directional response based on the last completed 6h return. This tests whether directional continuation exists only when volatility is expanding, without using breakout bands, candle location, serial sign balance, cross-sectional ranking, BTC beta/residual shocks, or any Phase217 rescue.

## Causality
At decision timestamp `t`, use returns through `t-1` only, with `pct_change(fill_method=None)`. For each alt compute `rv6 = sqrt(sum(r^2))` over the last 6 completed hourly returns and `rv72 = sqrt(mean(r^2 over 72))*sqrt(6)`, both ending at `t-1`. Define `vr = rv6/rv72`. Direction is sign of the completed 6h cumulative log return ending at `t-1`. Entry begins at `t`. No t-or-later price, funding, regime or statistic enters signal construction.

## Frozen universe / folds
ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. BTCUSDT is used only by the existing causal regime decomposition. Training folds are calendar 2023, 2024, 2025 independently. Validation/final holdout remains unopened.

## Exactly 8 frozen specs
Cartesian product:
- volatility-ratio threshold `V`: 1.25, 1.75
- absolute completed 6h return threshold `R`: 0.5%, 1.0%
- hold: 3h, 6h

Signal requires `vr >= V` and `abs(ret6) >= R`; direction is continuation of `ret6`. At most one live position per asset; ignore new signals while that asset is in its frozen hold. Equal notional across simultaneously eligible positions, normalized so portfolio gross exposure never exceeds 1.0.

## Costs / funding
Use the existing V98 Independent convention: base 0.07%, severe 0.14%, supersevere 0.28% round-trip-equivalent implementation convention. Apply identically to all specs/folds. Charge/credit realized PIT funding at crossed funding timestamps; funding is never a signal input.

## Required outputs
For every spec × fold × stress: total return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, best/worst trade, p01/p05/p50/p95/p99 trade tails, asset attribution/concentration, funding contribution, and bull/bear/sideways decomposition under the existing causal V98 regime convention.

## Mechanical training gate
Training-fold coherent only if base return >0 and base PF >1 independently in 2023, 2024 and 2025. A survivor must then clear severe/supersevere stress, tails/concentration/regime, causal/invariant and deterministic reproducibility audits before validation is considered.

## Anti-overfit
Exactly these 8 specs. No inversion/rescue, threshold expansion, post-hoc asset/regime filter, V99 information, or holdout access after results. Two deterministic executions must be byte-identical before decision.