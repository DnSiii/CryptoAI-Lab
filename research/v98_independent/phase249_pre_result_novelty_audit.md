# V98 Independent Phase249 — pre-result novelty / allocator audit

Status: PRE-RESULT / NO PHASE249 PNL INSPECTED.

## Distinction from prior V98 work

Repository-level namespace search before Phase249 performance found no V98 Independent implementation named or organized as risk parity, inverse-volatility allocation, equal-risk allocation, minimum-variance allocation, volatility weighting or dynamic allocator.

Phase249 is not:
- cross-sectional momentum/reversal;
- residual ranking;
- funding carry;
- breakout selection;
- volatility-compression alpha;
- market-regime filtering;
- crash-governor exposure switching.

It keeps the same four long Clean-4 assets and the same total target gross 1.00. Only the **capital allocation rule** changes.

## Frozen geometry

- 30-day / 720-hour realized volatility per asset.
- inverse-vol score only.
- daily decision at 23:00 UTC, next-open execution.
- long-only.
- target weights sum to 1.00.
- hard max 40% per asset with deterministic proportional redistribution.
- no leverage expansion.
- no asset deletion.
- no alternate estimator/window/cap after result.

## Scientific question

Does causal risk equalization improve **compounded terminal wealth**, not merely lower volatility, relative to the structural equal-weight core?

Because V98's North Star prioritizes compounded wealth, Phase249 cannot pass by producing a smoother but poorer equity curve. The frozen gate requires materially higher return/CAGR plus severe/supersevere superiority and chronological marginal robustness.

Failure closes this exact 30d inverse-vol / 40% cap allocator without rescue.
