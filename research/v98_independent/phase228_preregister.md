# V98 Independent — Phase228 preregistration

Status: **PREREGISTERED BEFORE RESULT OBSERVATION**

## Hypothesis

A genuinely orthogonal family to Phases225–227: **volatility-compression breakout continuation**. After an unusually compressed realized-volatility state, a confirmed price breakout may persist for a short horizon. This does not use cross-sectional residual rank, residual reversal/persistence, abnormal-volume selection, or V99 information.

## Frozen information set / causality

- Universe: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- 1h bars; decision features must end at `t-1`; execution at `open(t)`.
- Volatility state: trailing realized volatility computed only from returns available through `t-1`.
- Compression threshold is trailing/rolling and causal; no full-sample percentile.
- Breakout reference uses only highs/lows completed by `t-1`; no current-bar high/low.
- Exit is deterministic `open(t+h)`.
- Funding is realized PIT only while position is open.
- No overlapping position in the same asset. Portfolio gross exposure <= 1 at all times.
- 2026+ is forbidden/untouched.

## Frozen grid — exactly 8 specs

`compression_window ∈ {24,72}` hours × `breakout_window ∈ {24,72}` hours × `holding ∈ {4,8}` hours.

Compression rule: realized volatility over the last `compression_window` hours must be below the causal 20th percentile of that same volatility measure over the preceding 720 completed hours (excluding the current volatility observation from percentile estimation).

Breakout rule at `t-1`: close(t-1) > prior rolling `breakout_window` high => long; close(t-1) < prior rolling `breakout_window` low => short. The breakout reference excludes t-1 itself. No signal otherwise.

When multiple assets signal simultaneously, equal-weight only across new eligible signals subject to remaining gross capacity; existing positions are not rescaled.

## Evaluation frozen before execution

Chronological folds: calendar 2023, 2024, 2025 independently. Costs per round-trip notional: base 7 bp, severe 14 bp, supersevere 28 bp, plus realized PIT funding. Report per fold/spec/cost: return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, best/worst trade, p01/p05/p50/p95/p99, asset PnL contribution/max concentration, funding contribution, and bear/bull/sideways decomposition.

Deterministic reproduction must be byte-identical across two independent runs. Data firewall: all canonical price/funding timestamps `<2026-01-01`, monotonic and duplicate-free.

## Mechanical gate

A spec may survive only if, under **base cost in every one of 2023/2024/2025 independently**: return > 0, PF > 1, positive days > 50%, and trades >= 30. Severe/supersevere results are mandatory robustness evidence and may veto promotion if deterioration reveals pathological fragility. No averaging a failed year away.

If zero specs survive: `REJECT_FAMILY_NO_RESCUE`. No post-result asset deletion, regime filter, threshold adjustment, grid extension, tail clipping, or cost relaxation. If a spec survives, proceed directly to concentration/tail/regime/stress and reproducibility gates before any holdout consideration.

Champion remains unchanged until all preregistered gates pass.