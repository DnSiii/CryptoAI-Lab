# V99 R106 — Phase183 preregistration

Date: 2026-09-29
Status: PREREGISTERED / TRAIN-ONLY / NO HOLDOUT

## Hypothesis

Phase183 tests a scientifically distinct cross-asset mechanism: **beta-adjusted ETH residual dislocation mean reversion**, rather than the Phase182 equal-weight continuation/stress composite.

Using only already-admitted hourly BTCUSDT and ETHUSDT OHLCV, estimate ETH's rolling beta to BTC from the previous 168 completed hourly log returns. At decision hour t, all inputs must be available no later than t-1. Define the residual as ETH return minus lagged rolling beta times BTC return. Build a residual z-score using the previous 168 completed residuals, excluding the decision observation from its own normalization.

Frozen economic mapping before PnL:

- If residual z-score at t-1 >= +2.0: short ETH residual / long beta-scaled BTC hedge.
- If residual z-score at t-1 <= -2.0: long ETH residual / short beta-scaled BTC hedge.
- Otherwise: flat.
- Gross cap: 0.20. Scale both legs proportionally to satisfy the cap; do not add intentional directional BTC+ETH exposure.
- No alternative beta window, z window, threshold, sign, gross, weighting, asset substitution, smoothing, stop, take-profit, cooldown, or regime filter may be searched after PnL inspection.

The 168h window and |z|=2 trigger are fixed protocol choices for a weekly local relationship and a conventional rare-dislocation threshold; they are not selected from Phase183 PnL.

## Causality and data gates

1. Reuse only the Phase182 pair data after its integrity gate; do not ingest holdout market values.
2. Structural t-1: beta, residual history, z-score and target must depend only on completed observations strictly prior to the decision hour.
3. Require complete paired bars for every calculation; no forward fill/interpolation of market values.
4. Warm-up rows are unavailable, not imputed.
5. Exclusive TRAIN end remains 2024-01-18T00:00:00Z.
6. V16 Frozen and V99 Frozen are immutable and must be hash-checked around execution.

## Evaluation gates

Run deterministic TRAIN-only evaluation with the repository's chronological temporal folds. Require severe cost and exactly 2x severe supersevere. Report fold returns, max drawdown, trade/event count, exposure fraction, remove-best-event/hour, worst event/hour, and concentration by calendar segment. If the basic TRAIN gate survives, independently run the existing regime matrix and benchmark envelope before any holdout authorization.

Permanent rejection without retuning occurs if: any causality/integrity invariant fails; deterministic rerun differs; evidence is not chronologically stable; severe or supersevere economics fail; apparent edge is dominated by one fold/regime/event; or the benchmark envelope is not beaten on the preregistered criteria.

No holdout values may be parsed for selection or diagnosis. Holdout is permitted only after the candidate is formally frozen following all TRAIN gates.
