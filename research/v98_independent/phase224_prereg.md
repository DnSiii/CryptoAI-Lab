# V98 Independent — Phase224 preregistration

## Hypothesis
Extreme **realized perpetual funding dislocation** may contain a short-horizon convergence premium after the funding payment is known: unusually positive funding indicates crowded longs and motivates a short; unusually negative funding indicates crowded shorts and motivates a long. This is deliberately a funding-state hypothesis rather than another return-shock / volatility-shock rescue.

## Causality
At decision hour `t`, use only funding events whose timestamp is strictly `< t` and price bars completed through `t-1`. For each asset, take the most recent realized funding rate known before `t`; compute its trailing empirical z-score using only the preceding `L` realized funding observations, excluding the current event from the reference mean/std. A signal may occur only during the first hourly decision after a newly realized funding event. Entry is at `open(t)`; no high/low/close from bar `t` may enter the signal. Funding crossed during a live hold is charged/credited PIT according to position direction.

## Frozen universe / folds
- Tradable: ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- BTCUSDT is regime reference only, never traded by this family.
- Training folds evaluated independently: calendar 2023, 2024, 2025.
- 2026+ remains unopened and forbidden.

## Exactly 8 frozen specs
Cartesian product:
- funding history `L`: 63, 126 realized funding observations
- absolute funding z threshold `z`: 1.5, 2.5
- hold `H`: 4h, 8h

Direction is always convergence: funding z > threshold -> short; funding z < -threshold -> long. No direction inversion after results. At most one live position per asset; new signals while that asset is live are ignored. Equal notional across simultaneously eligible assets and gross portfolio exposure normalized to <=1.0.

## Costs / funding
Use the existing V98 Independent convention without change: base 0.07%, severe 0.14%, supersevere 0.28% round-trip-equivalent implementation convention. Realized PIT funding must be applied at every funding timestamp crossed by a position. No future funding value or future price may enter signal construction.

## Required outputs
For every spec × fold × stress: total return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, best/worst closed trade, p01/p05/p50/p95/p99 closed-trade tails, asset PnL attribution/concentration, funding contribution, and bull/bear/sideways regime decomposition under the existing causal V98 convention. Closed-trade tails must be asset-attributed and include exit turnover consistently with the current decision-grade V98 evaluator standard.

## Mechanical training gate
A spec is coherent only if base return > 0 and base PF > 1 independently in 2023, 2024 and 2025. A survivor is not promoted automatically: it must then pass reproducibility, cost-stress, tails/concentration, regime and invariant audits before any validation/holdout consideration.

## Anti-overfit / independence rules
- Exactly these 8 specs. No additional `L`, z, hold, asset filter or direction after results.
- No rescue by conditioning on a regime, asset, funding sign, weekday, hour or return state discovered from results.
- Phase223/Phase216 cell-level results may not tune this family.
- No V99 information may be used for selection.
- 2026+ cannot be opened unless a preregistered training survivor clears the complete audit chain.
- Two deterministic executions must be byte-identical before a scientific decision.
- Before implementation/execution, perform an explicit family-independence audit against prior V98 phases; if the same economic family was already closed, Phase224 becomes diagnostic-only rather than a rescue.
