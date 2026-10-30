# V98 Independent — Phase217 preregistration

## Hypothesis
Short-horizon **serial dependence in signed hourly returns** may identify asset-specific continuation versus reversal states without relying on price level, breakout bands, cross-sectional ranking, or BTC-residual shock magnitude. The hypothesis is that unusually persistent same-sign returns over completed bars contain conditional information about the next few hours; direction is continuation of the most recently completed return sign.

This is scientifically distinct from Phase216: no beta, BTC residual magnitude, volatility-shock z-score, or post-shock fade is used. It is also distinct from Phase213 candle-location continuation and Phase214 range breakout.

## Causality
For decision timestamp `t`, all features end at `t-1`. For each alt, compute over the last `L` completed hourly returns ending at `t-1`:
- `sign_balance = abs(sum(sign(r_i))) / L`, measuring directional persistence independent of return magnitude;
- direction = sign of the most recently completed hourly return `r(t-1)`.

A signal is eligible only when `sign_balance >= B` and the majority sign agrees with `sign(r(t-1))`. Entry begins at `t`. No OHLC value, return, funding observation, regime label, or statistic from `t` or later may enter signal construction. Missing returns are not forward-filled; subsequent evaluator must explicitly use `pct_change(fill_method=None)`.

## Frozen universe / folds
- ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- BTCUSDT only for the existing causal regime decomposition, never for signal selection.
- Training folds evaluated independently: calendar 2023, 2024, 2025.
- Validation/final holdout remains unopened.

## Exactly 8 frozen specs
Cartesian product:
- sign window `L`: 6h, 12h
- persistence threshold `B`: 0.50, 0.67
- hold: 3h, 6h

Direction: continuation of the agreed majority/latest sign. At most one live position per asset; signals while that asset is already in its frozen hold are ignored. Equal notional across simultaneously eligible positions, normalized so portfolio gross exposure never exceeds 1.0.

## Costs / funding
Use the existing V98 Independent convention: base 0.07%, severe 0.14%, supersevere 0.28% round-trip-equivalent implementation convention, applied identically to all specs/folds. Charge/credit realized PIT funding for each alt position at crossed funding timestamps. Funding is never a signal input.

## Required outputs
For every spec × fold × stress: total return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, best/worst trade, p01/p05/p50/p95/p99 trade tails, asset attribution/concentration, funding contribution, and bull/bear/sideways decomposition under the existing causal V98 regime convention.

## Mechanical training gate
A spec is training-fold coherent only if base return > 0 and base PF > 1 independently in 2023, 2024 and 2025. Passing this minimal gate is not promotion: any survivor must immediately clear severe/supersevere stress, tails/concentration/regime, causality/invariant and deterministic reproducibility audits before validation can be considered.

## Anti-overfit rules
- Exactly these 8 specs; no new windows, balance thresholds, directions, holds or filters after results.
- No inversion/rescue of a failed family.
- No post-hoc regime/asset filtering.
- No V99 information for tuning or selection.
- No validation/final holdout access unless a frozen training survivor clears the complete audit chain.
- Two deterministic executions must be byte-identical before any decision.
