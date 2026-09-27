# V99 R106 Phase162 — Funding Level/Change Disagreement

PREREGISTERED BEFORE ANY Phase162 PnL.

## Motivation
Phase159 (funding level dispersion), Phase160 (first difference) and Phase161 (second difference) all failed TRAIN with 0/4 healthy temporal folds. Do not tune, rescue, or sign-flip those failed transforms. Phase162 tests a scientifically distinct interaction: disagreement between the cross-sectional *level* and *change* of funding, intended to isolate crowded positioning whose current funding level and recent funding move point in opposite standardized directions.

## Frozen hypothesis
- TRAIN only: 2021-12-01 through 2024-01-18, identical to Phase159-161.
- Universe/data transport: exactly Phase159 PASS_DATA_ONLY assets and deterministic Binance Vision funding archive.
- For each valid funding event, construct cross-sectional median-centered funding level `L` and first difference `D`.
- Normalize L and D independently with trailing Exact-MAD168 using history shifted by one valid event.
- Interaction signal per asset: `I = zL * zD`.
- REVERSION only: target raw weight `-I`; normalize cross-sectionally to L1 <= 1.
- Execution lag: +1 hour after signal availability; causal past-only event matching <= 1h.
- No grid, no sign flip, no rescue, no parameter search.
- Same severe-cost TRAIN evaluator and four chronological temporal folds used by Phase159-161.
- Holdout rows used for feature construction/selection: 0/0.
- If base TRAIN gate fails, reject and do not run downstream stress gates.
- If it passes, freeze before severe/supersevere, regime matrix, tails/concentration, benchmark envelope and reproducibility.
- V16 Frozen and V99 Frozen are immutable.
