# V98 Independent — Phase229 preregistration

Status: **PREREGISTERED BEFORE RESULT OBSERVATION**

## Hypothesis
Scientifically distinct family: **causal intraday / time-of-week periodicity continuation**. Continuous crypto markets may exhibit persistent conditional return structure tied to recurring UTC participation/liquidity/funding cycles. This is not a volatility-compression breakout, residual rank/reversal/persistence, abnormal-volume selector, or V99-derived signal.

## Frozen information set / causality
- Universe: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- 1h bars; all signal estimates end at `t-1`; execution at `open(t)`; deterministic exit at `open(t+h)`.
- For each asset and candidate bucket, estimate the mean signed open-to-open return using **only prior completed occurrences** of that bucket.
- Bucket definitions are UTC and frozen: hour-of-day (24 buckets) or hour-of-week (168 buckets).
- Lookback is occurrence-count based and trailing; current/future observations never enter the estimate.
- Signal: long if trailing bucket mean > 0, short if < 0; no magnitude threshold and no post-result bucket deletion.
- Funding: realized PIT only while position is open. No overlapping position in same asset. Portfolio gross exposure <=1; simultaneous eligible signals equal-weight subject to remaining gross capacity.
- 2026+ forbidden/untouched.

## Frozen grid — exactly 8 specs
`bucket ∈ {hour_of_day, hour_of_week}` × `lookback_occurrences ∈ {12,24}` × `holding ∈ {1,4}` hours.

Minimum history equals the selected lookback: no trade until a bucket has the full trailing occurrence count. Every eligible bucket is traded according to its causal sign; there is no ex-post selection of hours/days/assets.

## Evaluation frozen before execution
Chronological folds: calendar 2023, 2024, 2025 independently. Costs per round-trip notional: base 7 bp, severe 14 bp, supersevere 28 bp, plus realized PIT funding. Report per fold/spec/cost: return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, best/worst trade, p01/p05/p50/p95/p99, asset PnL contribution/max concentration, funding contribution, and bear/bull/sideways decomposition.

Deterministic reproduction must be byte-identical across two independent runs. Data firewall: canonical price/funding timestamps `<2026-01-01`, monotonic and duplicate-free. Explicit invariant: each bucket estimate at decision time must be reproducible from rows strictly earlier than `t`.

## Mechanical gate
A spec survives only if under base cost in **each** of 2023/2024/2025 independently: return >0, PF>1, positive days>50%, trades>=30. Severe/supersevere are mandatory and may veto pathological cost fragility. No averaging a failed year away.

If zero survive: `REJECT_FAMILY_NO_RESCUE`. No post-result bucket/asset deletion, sign flip, threshold addition, lookback extension, regime filter, tail clipping, or cost relaxation. A survivor proceeds immediately to concentration/tail/regime/stress/reproducibility gates before any holdout consideration.

Champion remains unchanged until every preregistered gate passes.