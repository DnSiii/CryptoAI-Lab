# V98 Independent — Phase220 preregistration

Status: **FROZEN BEFORE RESULTS**

## Hypothesis
Test a scientifically distinct, market-neutral cross-sectional funding-dispersion hypothesis: among ETHUSDT, BNBUSDT, XRPUSDT and SOLUSDT, unusually expensive perpetual funding can proxy crowded long positioning. At each eligible decision time, short the asset with the highest trailing standardized funding pressure and long the asset with the lowest, but only when the cross-sectional funding-score spread is sufficiently large. This is not a rescue of Phase219: Phase219 was single-asset post-settlement time-series mean reversion after absolute funding extremes; Phase220 is contemporaneous cross-sectional relative-value dispersion with paired dollar-neutral exposure.

## Data firewall and causality
- Training/selection data only: timestamps strictly `<2026-01-01`.
- 2026+ remains untouched holdout.
- Universe frozen: ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT; BTCUSDT only for regime labels, never selection.
- At decision hour `t`, every funding observation and price-derived feature must be known by `t-1h` or earlier.
- Funding events are joined point-in-time by `fundingTime <= t-1h`; no backfill from future events.
- Use `pct_change(fill_method=None)` wherever returns are computed.
- Missing/stale funding cannot be forward-filled across an unknown future event boundary; eligibility requires valid trailing history.

## Frozen signal
For each asset, construct trailing funding pressure as the mean of the last `N` observed funding events available by `t-1h`, divided by its trailing robust scale (MAD with deterministic epsilon guard). Rank the four scores cross-sectionally. Enter only when `max(score)-min(score) >= S`. Long the minimum-score asset and short the maximum-score asset, each at 0.5 absolute weight. No BTC directional overlay, no regime filter, no asset-specific threshold.

Exactly 8 specs, frozen Cartesian grid:
- `N ∈ {21, 63}` funding events
- `S ∈ {1.0, 1.5}` score-spread threshold
- `hold ∈ {4h, 8h}`

No overlapping position in the same asset. Gross exposure <= 1.0. A pair is entered only when both legs are simultaneously eligible. Deterministic tie-break: lexical symbol order.

## Economics and costs
Account realized price PnL plus actual point-in-time funding cashflows on both legs during each holding interval with correct long/short sign. Apply round-trip trading costs to both legs under the existing V98 Independent cost schedule: base, severe, supersevere. No cost waiver for paired trades.

## Chronological evaluation
Evaluate all 8 specs independently on frozen calendar folds 2023, 2024, 2025. No random CV. No use of 2026+ in feature calibration, thresholds, ranking, selection, diagnostics used for decisions, or promotion.

Required per fold and stress: return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, p01/p05/p50/p95/p99 tails, worst/best trade, max asset concentration, funding contribution, and BTC-defined bull/bear/sideways regime breakdown.

## Mechanical gate
A spec is training-fold coherent only if, under **base** costs, every one of 2023/2024/2025 has return > 0 and Profit Factor > 1. Severe/supersevere must be reported and analyzed and returns must degrade monotonically with costs. Promotion requires reproducible deterministic output plus acceptable drawdown, tails, concentration and regime robustness; merely passing the minimal coherence gate is not sufficient.

## Anti-overfit constraints
No sign inversion, threshold rescue, asset deletion, regime cherry-pick, alternative hold after results, or V99-derived tuning. If 0/8 specs pass the frozen coherence gate, reject the family and move to a genuinely distinct hypothesis. Any code change that changes signal semantics after results requires a new phase/preregistration, not a Phase220 rerun.
