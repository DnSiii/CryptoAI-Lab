# V99 R106 Phase81 — Top-capital vs global-crowd divergence preregistration

## Status
PRE-REGISTERED BEFORE EXECUTION. Train-only gate. Untouched holdout remains prohibited.

## Hypothesis
A cross-sectional divergence between the long/short **position ratio of top traders** and the **account ratio of the global population** may identify assets where informed/large-position capital is directionally displaced from broad crowd breadth. This is distinct from Phase67 (top-trader position vs top-trader account disagreement) and Phase79 (top-trader account vs global account divergence).

## Frozen specification
- Source: Binance USD-M daily metrics archives already audited in Phase63.
- Required same-hour fields: `sum_toptrader_long_short_ratio` and `count_long_short_ratio`.
- Both values must be present, finite, and strictly positive in the same native hourly observation.
- Raw signal: `log(sum_toptrader_long_short_ratio / count_long_short_ratio)`.
- Causality: apply exactly one-hour `shift(1)` before portfolio construction.
- Direction: continuation; larger positive divergence ranks long, negative divergence ranks short through the existing Phase31 cross-sectional weight constructor.
- Alpha gross: fixed 0.20.
- Cost gate: severe cost first.
- Missing archives/observations are never filled and missing hours are never bridged.
- Every downloaded archive must pass published SHA256 and ZIP CRC checks.

## Anti-overfit constraints
Exactly one hypothesis. No sign flip, no horizon search, no threshold/grid, no winsorization, no smoothing, no weight search, no rescue after seeing the result. Selection and diagnostics are chronological train-only with existing temporal folds and robust ex-top1% diagnostic.

## Decision gate
PASS only if the existing stable-train diagnostic passes. A PASS freezes this exact specification for supersevere/regime/benchmark validation before any untouched holdout. A FAIL is permanently rejected and cannot be retuned.

V16 Frozen and V99 Frozen must not be modified.