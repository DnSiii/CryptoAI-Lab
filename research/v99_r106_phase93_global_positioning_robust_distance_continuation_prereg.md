# V99 R106 Phase93 — Global positioning robust-distance continuation

## Status
PRE-REGISTERED BEFORE ANY PHASE93 PNL.

Phase92 is permanently rejected. Phase93 is not a sign flip, rescue, threshold sweep, or parameter grid. It tests a distinct economic mechanism: whether extreme relative global positioning contains continuation rather than mean reversion.

## Frozen hypothesis
- Native source: Binance USD-M daily metrics `count_long_short_ratio` only.
- Use only archives/date coverage already admitted by the Phase63 train-only data audit; missing archives remain missing.
- Parse only positive finite ratios; transform to log level.
- Causality: shift the feature by exactly one hourly observation (`t-1`) before target construction.
- At each timestamp require >=10 simultaneous assets.
- Compute simultaneous cross-sectional median and MAD. If MAD is non-finite or <=1e-12, exposure is zero.
- Robust distance: `z=(x-median)/MAD`.
- Fixed continuation mapping: `raw=+tanh(z)`; no fitted scale and no threshold.
- L1-normalize simultaneous raw scores; fixed alpha gross = 0.20.
- Costs: severe for the train-alpha gate.
- Evaluation: same chronological train endpoint, temporal folds, stable_train diagnostic, tail robustness and anti-overfit gate used by Phase92.
- Selection is train-only. Holdout MUST NOT be listed, parsed, inspected, or optimized.
- No grid, sign search, threshold search, rescue, post-result retuning, or Phase93 alternative.
- V16 Frozen and V99 Frozen must remain byte-identical.

## Decision rule
If the canonical train-only diagnostic passes, freeze this exact specification and advance without modification through supersevere cost, regime matrix, benchmark envelope and reproducibility before any untouched holdout gate. If it fails, permanently reject Phase93 and move to a genuinely orthogonal mechanism.
