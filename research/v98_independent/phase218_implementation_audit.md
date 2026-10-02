# V98 Independent — Phase218 implementation audit

## Scope
Independent pre-result audit of the Phase218 evaluator and deterministic workflow against the frozen preregistration. No Phase218 result was inspected when this audit was written.

## Frozen grid
Evaluator contains exactly the preregistered Cartesian product: `V ∈ {1.25,1.75}`, `R ∈ {0.005,0.01}`, `hold ∈ {3,6}`, hence exactly 8 specs. Universe is ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT; BTCUSDT is restricted to causal regime decomposition.

## Causality
Hourly return uses `pct_change(fill_method=None)`. Both realized-volatility legs are rolling statistics shifted by one completed bar: 6-hour sum-of-squares and 72-hour mean-of-squares scaled to 6 hours. The completed 6h log return is also shifted by one bar. Therefore a decision at `t` uses information through `t-1`; exposure begins at `t`. New signals are ignored while an asset remains inside its frozen holding interval.

## Exposure / execution
Simultaneously eligible positions are equal-weight normalized whenever gross exposure would exceed 1.0. PnL is generated from lagged position against open-to-open hourly return. Turnover is charged under the frozen base/severe/supersevere cost levels. Realized funding is aligned to crossed hourly timestamps and applied to lagged position; it is not a signal input.

## Data firewall
Price and funding loaders reject timestamps at or after 2026-01-01, duplicates, and non-monotonic indexes. Workflow independently rebuilds training-only canonical prices and repeats the `<2026` firewall. Calendar folds 2023, 2024 and 2025 are evaluated independently with data sliced to each fold stop. Validation/final holdout is not referenced by evaluator or workflow.

## Diagnostics / gate
Every spec × fold × stress emits total return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, best/worst trade, p01/p05/p50/p95/p99 tails, asset attribution/concentration, funding contribution and causal bull/bear/sideways metrics. Workflow executes twice and requires byte-identical SHA output. Mechanical training coherence remains base return > 0 and base PF > 1 in each of 2023, 2024 and 2025; stress monotonicity is asserted before any promotion can be considered.

## Audit conclusion
Implementation is consistent with the frozen Phase218 hypothesis and anti-overfit discipline. No rescue, inversion, threshold expansion, post-hoc asset/regime filtering, V99 information, or holdout access was introduced. Result-dependent promotion/rejection remains pending deterministic workflow completion.
