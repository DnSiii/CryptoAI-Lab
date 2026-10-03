# V98 Independent Phase222 — preregistration

## Hypothesis

**Intraday range-compression breakout continuation**, price-only and scientifically distinct from Phase221's BTC-beta residual cross-sectional ranking. Hypothesis: after unusually compressed realized intraday range, a causal break beyond the prior completed range boundary may carry short-horizon continuation large enough to survive realistic execution costs. No Phase221 parameter/result is used to select Phase222 settings.

## Frozen universe and evidence boundary

Universe: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT, using the existing V98 Independent canonical 1h training dataset. Training/evaluation folds are exactly calendar 2023, 2024, 2025. All timestamps >= 2026-01-01 UTC remain forbidden/unopened. Data must be rebuilt independently by the workflow and firewall-checked before evaluation.

## Causal feature definition

At decision hour `t`, only bars completed through `t-1` may enter features. For asset i:

- `range24(t-1) = (rolling_max(high,24) / rolling_min(low,24) - 1)` over completed bars ending t-1.
- `range168_median(t-1)` is the rolling median of `range24` over exactly 168 completed observations, min_periods=168.
- Compression is `range24 <= c * range168_median`, where frozen `c` is 0.55 or 0.70.
- Prior boundary is the 24h completed-bar high/low ending t-1. Long trigger: current hour open is above prior 24h high; short trigger: current hour open is below prior 24h low. The current open is observable at execution time; no current high/low/close is permitted in the signal.
- Position is entered at current open plus explicit execution cost and held for frozen H hours, with no overlapping position in the same asset. No stop/target optimization.

## Exactly eight frozen specs

Cartesian product, no additions/removals after results:

- compression `c in {0.55, 0.70}`
- hold `H in {4, 8}` hours
- direction `D in {continuation, symmetric}`

`continuation`: trade both long upper-break and short lower-break exactly as defined. `symmetric`: same triggers but require the 24h close-to-close return through t-1 to have the same sign as the break (positive for long, negative for short). This is a preregistered confirmation rule, not post-result rescue.

## Portfolio/exposure

Each active asset position receives equal notional among simultaneously active positions; gross portfolio exposure <= 1.0 at every hour. No leverage. If multiple triggers occur at one timestamp, deterministic alphabetical asset order is used only for stable bookkeeping; weights are equal. No same-asset overlap during H-hour hold.

## Costs and funding

Use the same V98 Independent realistic cost engine and PIT funding accounting used by prior phases. Funding may be charged/credited only when its timestamp occurs during an actually open position and was not known before it occurred. Evaluate all eight specs under base, severe, and supersevere cost schedules without modification. Stress returns must be monotone non-increasing base -> severe -> supersevere; violation invalidates the run.

## Required outputs

For every spec x fold x stress: compounded return, max drawdown, Profit Factor, payoff, win rate, positive-day fraction, trade count, p01/p05/p50/p95/p99 trade tails, worst/best trade, maximum asset concentration, per-asset return contribution, funding contribution, and bull/bear/sideways regime return/PF/MDD/payoff/win-rate/positive-days. Record deterministic payload SHA256.

## Mechanical training gate

A spec is training-fold coherent only if **base return > 0 and base PF > 1 in each of 2023, 2024, 2025**. Passing this gate does not authorize opening the holdout; it only permits the next preregistered robustness gate. Zero passing specs => `REJECT_FAMILY_NO_RESCUE`.

## Reproducibility/invariants

Workflow must: rebuild data from source; assert no canonical timestamp >=2026; assert monotonic unique timestamps; assert exactly eight specs; assert feature windows end at t-1; assert current-bar high/low/close are absent from signal construction; assert gross exposure <=1; execute evaluator twice and require byte-identical SHA256; verify complete metrics and monotone stress response.

## Anti-overfit boundary

No Phase222 result may justify changing compression thresholds, 24h/168h windows, holds, confirmation, universe, direction, cost schedule, or folds. If rejected, any next family must be scientifically distinct and preregistered first. Holdout remains untouched until a separately preregistered promotion protocol authorizes it.
