# V98 Independent — Phase226 preregistration

Status: **PREREGISTERED — RESULT BLIND**. Holdout 2026+ remains CLOSED.

## Scientific hypothesis
After Phase225 rejected abnormal-volume reversal, test a distinct mechanism: **cross-sectional idiosyncratic momentum persistence**. At each completed bar t-1, estimate each altcoin's trailing return residual versus BTC over a fixed trailing window, rank residual momentum cross-sectionally, and hold the strongest positive residual long and strongest negative residual short from open(t) for a fixed horizon. This is continuation, not reversal; volume is not a signal input and realized funding is accounting-only.

## Frozen universe and causality
- Universe: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT; BTC is benchmark and may be flat in the long/short residual book.
- Training folds only: calendar 2023, 2024, 2025. No timestamp >= 2026-01-01 may enter features, prices, funding, evaluation, diagnostics, or selection.
- Signal information ends at t-1; entry=open(t); exit=open(t+H).
- Residual momentum for asset i: trailing W-hour asset log return minus beta_i(t-1)*BTC trailing W-hour log return. beta_i is estimated only from completed hourly returns in the immediately preceding 30 days, excluding the entry bar and all future observations.
- Require finite benchmark/asset history and beta estimate before ranking. No forward fill across missing price bars.

## Exactly 8 frozen specifications
Cartesian product:
- W in {24h, 72h}
- cross-sectional absolute residual threshold Q in {0.010, 0.020}
- holding H in {4h, 8h}

At each eligible t, among non-BTC assets exceeding +Q choose at most the single largest residual long; among those below -Q choose at most the single most-negative residual short. If both exist, allocate 0.5 gross each; if one side exists, allocate at most 0.5 gross and leave unused capacity in cash. Existing positions are never resized. No same-asset overlap; total gross exposure <=1 at all times.

## Economics and costs
- Realized Binance USD-M funding is accounting-only, point-in-time, applied only when a held position crosses an actual settlement timestamp; no forecast funding in the signal.
- Round-trip trading cost stresses: base=7 bp, severe=14 bp, supersevere=28 bp, charged on notional round trip consistently with prior V98 decision-grade evaluators.
- Cost monotonicity is mandatory: increasing costs cannot improve net return/PF mechanically.

## Required outputs per spec × year × stress
Net return, max drawdown, Profit Factor, payoff ratio, win rate, positive-days %, closed trades; trade p01/p05/p50/p95/p99, worst/best trade; signed contribution and trade count by asset; max absolute asset contribution concentration; BTC bull/bear/sideways attribution using the existing V98 causal regime convention; funding and trading-cost totals.

## Mechanical training gate
A spec survives only if, under **base costs in each of 2023, 2024, and 2025 separately**: net return >0, PF>1, positive-days>50%, and >=30 closed trades/year. Severe/supersevere are mandatory robustness diagnostics and must show economically coherent degradation. Any invariant, chronology, funding, exposure, fold, reproducibility, or data-firewall failure invalidates execution rather than creating a tunable result.

## Anti-overfit / disposition
Exactly these 8 specs may be evaluated. No threshold/horizon/window/asset/year/regime/tail exclusion may be altered after result observation. No V99 evidence may tune or select V98. If zero specs survive, disposition is `REJECT_FAMILY_NO_RESCUE`. If survivors exist, they require independent reproducibility plus tails/concentration/regime audit before any untouched-holdout protocol can be considered.
