# V99 R106 Phase103 — OI acceleration train-only preregistration

## Status
Pre-registered before any Phase103 PnL is computed or inspected.

## Hypothesis
Phase102 established that raw 24h OI participation impulse is not a viable continuation alpha. Phase103 tests a distinct fixed hypothesis: **acceleration in participation**, rather than its level/impulse, may identify cross-sectional continuation. For each asset/hour, compute log(sum_open_interest_value), its 24h change, then the change in that 24h impulse versus 24 hours earlier: `(logOI_t-logOI_t-24) - (logOI_t-24-logOI_t-48)`. Shift the resulting feature by one hour before portfolio construction (`t-1`). Cross-sectionally normalize each hour by median/MAD, apply tanh, L1-normalize, and trade continuation in the sign of OI acceleration.

## Fixed specification
- Source: Binance USD-M daily metrics `sum_open_interest_value`, checksum/CRC verified.
- Feature: 24h OI impulse acceleration = `delta24(logOI) - delta24(logOI).shift(24)`.
- Causality: feature shifted by exactly 1 hour before signal use.
- Cross-sectional transform: hourly median/MAD robust z-score; require >=10 simultaneous assets and positive MAD; `tanh(z)`; L1 normalization.
- Direction: continuation toward positive OI acceleration.
- Alpha gross: 0.20 fixed.
- First cost gate: severe cost per side from canonical execution assumptions.
- Selection/evaluation: chronological train-only diagnostic and temporal folds already used by the R106 train-alpha harness.
- Missing metric archives remain missing; no filling from future or alternate periods.

## Anti-overfit constraints
Single hypothesis only. No parameter grid, horizon sweep, threshold sweep, sign flip, rescue, or post-result retuning. Phase103 is permanently rejected if the existing `stable_train` gate fails. A PASS freezes this exact specification for supersevere, regime matrix, benchmark-envelope and reproducibility gates before any untouched holdout may be parsed.

## Integrity constraints
V16 Frozen and V99 Frozen are read-only and must remain byte-identical. Holdout must not be listed, parsed, scored, or used for selection during this phase.