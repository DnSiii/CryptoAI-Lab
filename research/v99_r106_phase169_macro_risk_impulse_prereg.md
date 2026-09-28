# V99 R106 Phase169 — Macro risk impulse TRAIN-only alpha preregistration

Status: PREREGISTERED BEFORE ANY Phase169 PnL.

## Dependency
Phase168 must be PASS_DATA_ONLY. Phase169 must abort otherwise.

## Single frozen hypothesis
External macro stress changes may condition crypto risk appetite. Test one composite only; no grid, no sign search, no dropping series after PnL.

- Frozen panel: FRED DGS2, DGS10, DTWEXBGS, VIXCLS. DFF remains audited context but is excluded from the impulse because it is stepwise policy state rather than a market impulse.
- Daily values are fetched only inside TRAIN: 2021-12-01 <= observation date < 2024-01-18. Missing native business-day observations are not interpolated in the DATA audit; for the hourly causal feature, each series uses only its latest finite observation whose calendar date is strictly before the crypto hour's UTC date. Thus same-day macro observations are never used.
- Per-series impulse is the 5-business-observation change of that strictly-prior daily series, standardized causally with expanding mean/std using only earlier impulse observations (minimum 60 observations), then clipped to [-4,4].
- Frozen risk-off orientation: +VIX change, +USD broad-index change, +2Y yield change, +10Y yield change are risk-off. Composite = equal-weight mean of available standardized components, requiring all four.
- Frozen alpha direction: risk-off composite > 0 -> short crypto equally; risk-off composite < 0 -> long crypto equally. Magnitude = tanh(abs(composite)); gross cap 0.20; equal weights across currently executable V15 universe. No asset selection.
- Entire target is additionally shifted one crypto hour (t-1) before execution, even though macro information is already restricted to prior calendar dates.
- Selection/evaluation is TRAIN only under severe cost. Holdout values must not be fetched, parsed, scored or inspected.

## Frozen TRAIN gate
Use the existing Phase47 diagnostic discipline: >=720 active TRAIN hours; TRAIN ROI > 0; PF > 1.08; robust mean without top 1% > 0; at least 3 eligible temporal folds and at least 3 healthy folds. A healthy fold requires ROI > 0, PF > 1 and robust mean without top 1% > 0.

## Decision
PASS freezes this exact mechanism for a later independent supersevere/regime/concentration/benchmark/reproducibility gate before any untouched holdout. FAIL permanently rejects this exact mechanism; no horizon, sign, threshold, component or gross retuning from observed PnL.

V16 Frozen and V99 Frozen are read-only.