# V98 Independent — Phase208 preregistration

## Hypothesis
**Idiosyncratic volatility-compression breakout continuation.** After an unusually compressed asset-specific volatility state, a causal breakout from the prior 24h range may carry short-horizon continuation because information/liquidity adjustment is delayed. This is distinct from Phase207 residual cross-sectional momentum and Phase206 funding dislocation.

## Data firewall
- Branch: `research/v98-independent-zero` only.
- Assets: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT; canonical 1h data only, strictly `<2026-01-01`.
- Folds: calendar 2023, 2024, 2025, scored separately; pre-fold history may be used only for causal warm-up.
- Validation/final holdout remains unopened and must not influence implementation, selection, thresholds or promotion.
- Every feature at decision time t uses information available no later than t-1 close. Orders enter at t open; no same-bar lookahead.

## Fixed signal
For each asset independently:
1. Compute hourly log returns.
2. `rv_W(t-1)` = standard deviation of returns over the immediately preceding W hours, W in {24,72}.
3. Compare `rv_W(t-1)` with its causal empirical percentile over the preceding 90 calendar days (2160 hourly observations, excluding current hour).
4. Compression is true when percentile <= Q, Q in {0.10,0.25}.
5. Prior range is the highest high / lowest low over the 24 completed hours ending at t-1.
6. Long at t open if compression is true and t-1 close > prior-24h high computed excluding t-1; short symmetrically if t-1 close < prior-24h low excluding t-1.
7. Hold exactly H hours, H in {8,24}; no overlapping position in the same asset. No post-hoc stop, take-profit, regime filter, asset filter or signal inversion.

## Closed grid — exactly 8 specs
Cartesian product: W {24,72} × Q {0.10,0.25} × H {8,24}. No additional parameter search.

## Economics
Use the same V98 Independent base/severe/supersevere round-trip execution-cost schedule and realized funding accounting already frozen for recent phases. Funding must be aligned causally to the position interval; missing funding is not imputed. Position sizing/equity aggregation must remain consistent with the existing V98 evaluator convention.

## Required outputs per spec/fold/cost
Return, max drawdown, Profit Factor, payoff, win rate, positive-day fraction, trade count, best/worst trade, p01/p05/p50/p95/p99 full-trade PnL tails, asset contribution/concentration, and bull/bear/sideways regime decomposition. Report full-trade economics including entry, holding funding and exit.

## Reproducibility/invariants
- Assert monotonic unique timestamps and strict `<2026-01-01` firewall.
- Assert scoring begins exactly at fold start and no warm-up position leaks into a fold.
- Run evaluator twice from the same frozen inputs and require identical deterministic payload/result hash.
- Any code/integrity correction discovered before economic inspection is allowed only if documented and does not alter the frozen hypothesis/grid.

## Mechanical promotion discipline
A candidate cannot advance unless its base-cost behavior is positive and coherent across all three chronological folds, with PF > 1 in each fold, acceptable drawdown/tails/concentration, and no single regime/asset explaining the aggregate edge. It must remain economically credible under severe and supersevere stress. Exact downstream gate thresholds already established by V98 governance remain binding; this preregistration does not weaken them.

If the family fails, reject it without rescue/tuning and move to a scientifically distinct hypothesis. Do not inspect validation/final holdout.
