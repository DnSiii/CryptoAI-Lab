# V98 Independent Phase222 — pre-result implementation audit

Audit completed after recovering the frozen preregistration and before observing any Phase222 result.

## Fidelity and anti-overfit
- Exactly 8 frozen specs: compression {0.55,0.70} × hold {4,8} × direction {continuation,symmetric}.
- Universe remains BTC/ETH/BNB/XRP/SOL; folds remain 2023/2024/2025; >=2026 is rejected by both price and funding loaders.
- No threshold, window, hold, asset, side, cost, regime, or gate was selected from Phase222 outcomes.

## Causality audit
- Prior 24h high/low use `high.shift(1)` / `low.shift(1)` before rolling, so boundaries end at t-1.
- `range24` is built from those completed-bar boundaries; its 168-observation median therefore also ends at t-1.
- Symmetric confirmation uses `close.shift(1)/close.shift(25)-1`, ending at t-1.
- The only current-bar field consulted by signal(t) is `open(t)`, as preregistered. Current high/low/close are not used.
- Position PnL uses shifted weights against open-to-open returns, preventing same-open information from earning a prior interval return.

## Exposure, costs and funding
- Same-asset overlap is prevented by a deterministic per-asset active-until clock.
- Concurrent positions are equal-notional via normalization by active gross count; asserted portfolio gross exposure <=1.
- Established adjacent V98 cost schedule is preserved: base 7 bp, severe 14 bp, supersevere 28 bp per turnover unit.
- Funding is PIT carry only: hourly settlement buckets are applied to positions already held (`weight.shift(1)`), never to signal construction.

## Required diagnostics and validation
- Evaluator emits return, MDD, PF, payoff, win rate, positive days, trades, p01/p05/p50/p95/p99, worst/best trade, asset contribution/concentration, funding contribution, and bull/bear/sideways diagnostics.
- Separate namespaced validator enforces 8 specs, exact folds/stresses, required metrics, concentration bounds, monotone base→severe→supersevere returns, mechanical 2023/24/25 gate, and optional byte-identical double-run comparison.

## Audit conclusion
Implementation is eligible for execution subject to successful runtime validation and deterministic double-run reproduction. No Phase222 result has been observed in this audit. Champion remains unchanged; holdout remains closed. No V16/V99/paper artifact is involved.
