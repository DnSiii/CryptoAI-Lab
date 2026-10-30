# V98 Independent — Phase206 preregistration

Date frozen: 2026-10-01
Status: **PREREGISTERED / NO RESULTS INSPECTED**
Scope: V98 Independent only; validation/final holdout forbidden.

## Scientifically distinct hypothesis

**Cross-asset funding-dislocation mean reversion.** Extreme perpetual funding is a direct positioning/carry variable, not a transformation of the failed price-path, volatility, CLV, volume-shock, or BTC→alt lead/lag families. Hypothesis: unusually positive funding predicts subsequent underperformance (short); unusually negative funding predicts subsequent outperformance (long), after paying realized funding and trading costs.

This is tested as a standalone causal family, not as a rescue/filter for any prior V98 family.

## Frozen universe and data

Universe: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. Use only the V98 Independent canonical/archive data with timestamps `<2026-01-01`. Funding observations must be timestamp-aligned causally: at decision time `t`, only funding observations whose publication/settlement timestamp is strictly known by `t-1` may enter the signal. No forward-filled future funding, no future cross-sectional ranks, no 2026+ data.

Chronological evaluation folds: calendar 2023, 2024, 2025, reported separately and aggregate only after separate fold metrics are retained. Validation/final holdout remains untouched.

## Frozen signal family — 8 specs

For each asset, compute a trailing funding z-score using only funding known by `t-1`. Grid is fixed before results:

- lookback: 30d or 90d of available funding observations;
- absolute entry z: 1.5 or 2.5;
- hold: 8h or 24h.

Eight specs = 2 × 2 × 2. Signal direction is contrarian: z >= threshold => short; z <= -threshold => long. No pyramiding in the same asset. A new position may be opened only after the prior fixed holding period has completed. No post-result threshold changes.

## Execution and costs

Entry at the first executable hourly bar after the causal signal. Exit after the frozen hold. Include realized price PnL plus all funding cashflows that occur while the position is open, with correct long/short sign. Apply the existing V98 Independent base, severe, and supersevere round-trip execution-cost schedules without weakening them.

## Required metrics

For every spec × fold × cost level report at minimum: net return, max drawdown, Profit Factor, payoff, win rate, positive-days fraction, trade count, complete-trade PnL p01/p05/p50/p95/p99, best/worst trade, per-asset returns and max asset concentration. Report bull/bear/sideways regime metrics using the already-established V98 regime definition; regime labels may diagnose but may not select/tune this family.

## Integrity / reproducibility gates

1. Rebuild training-only data and assert all evaluated timestamps `<2026-01-01`.
2. Assert monotonic unique hourly indices and exact frozen universe.
3. Assert each signal's newest funding input timestamp is <= signal information cutoff (`t-1`).
4. Assert complete-trade tails reconcile to the same trade ledger used for PF/payoff/win rate.
5. Run evaluator twice from the same rebuilt inputs and require byte-identical deterministic payload/report SHA256.
6. Preserve and report known source gaps rather than silently imputing them.

## Promotion discipline

No holdout opening from a merely interesting result. A candidate can advance only if the preregistered family demonstrates economically positive, fold-stable behavior under base costs, remains credible under severe/supersevere stress, avoids pathological concentration/tail dependence, and passes all causality/reproducibility invariants. Isolated regime, asset, year, or threshold wins are insufficient. If the family fails, reject without inversion/rescue and move to a new orthogonal hypothesis.

## Forbidden

No V16 Frozen modifications. No V99 Frozen or V99 research branch/workflow/report/paper modifications. No V99 evidence for V98 tuning/selection. No validation/final holdout inspection. No post-hoc grid expansion, regime gating, asset cherry-picking, or cost weakening.