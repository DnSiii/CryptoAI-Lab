# V98 Independent Phase213 — preregistration

Status: **FROZEN BEFORE RESULTS**

## Hypothesis

Test a causal **close-location value continuation** mechanism distinct from Phase212 exhaustion reversal. A candle that closes persistently near one edge of its own range while its body direction agrees may represent directional order-flow persistence rather than exhaustion. Phase213 tests continuation, not reversal, and does not reuse Phase212 outcomes to select assets/regimes.

## Information set / causality

At decision timestamp `t`, features may use completed candles only through `t-1`. For each alt independently compute on `t-1`:

- `CLV = ((close-low) - (high-close)) / max(high-low, eps)`, bounded approximately [-1,1].
- signed body fraction `BODY = (close-open) / max(high-low, eps)`.
- rolling range normalization uses a trailing window ending at `t-1`; no centered/forward window.

Long when CLV and BODY are both positive beyond frozen thresholds and normalized range is sufficiently large; short symmetrically when both are negative. Entry is at `t` open/available causal execution price used by the V98 harness. Fixed holding horizon; no overlapping position for the same asset. Funding is charged only when actually crossed/held according to existing PIT funding implementation.

## Frozen grid — exactly 8 specs

Cartesian product:

- trailing range window `L`: {72h, 168h}
- absolute CLV threshold: {0.60, 0.75}
- hold: {3h, 6h}

Fixed for all specs:

- `abs(BODY) >= 0.35`
- previous candle true range >= rolling median true range over L
- symmetric long/short rules
- ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT only; BTC may be used only for the pre-existing regime label, never as a tuned signal.

No additional threshold, asset subset, regime filter, direction flip, rescue grid, or post-hoc inversion is permitted after results.

## Evaluation protocol

Chronological training folds remain 2023, 2024, 2025. Validation/final holdout remains unopened. Data firewall requires timestamps `<2026-01-01`, monotonic unique timestamps and training-only rebuild. Preserve realistic realized funding and the established V98 round-trip cost levels: base 0.07%, severe 0.14%, supersevere 0.28%.

For every spec/fold/cost report at minimum: total return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, best/worst trade, p01/p05/p50/p95/p99 tails, per-asset returns/funding contribution/max concentration, and bull/bear/sideways regime metrics.

## Mechanical gate

A spec is training-fold coherent only if **base return > 0 and base PF > 1 in each of 2023, 2024 and 2025**. Passing this minimal gate does not itself promote a champion: any survivor must then face severe/supersevere robustness, concentration/tails/regime audit, reproducibility and subsequent preregistered validation gates before any holdout consideration.

If zero of eight specs pass, reject the family without rescue and move to a scientifically distinct hypothesis.

## Reproducibility

Evaluator output must be deterministic and run twice from the same rebuilt training-only inputs; result-file SHA256 must match exactly before interpreting the family.
