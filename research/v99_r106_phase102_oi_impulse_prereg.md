# V99 R106 Phase102 — OI impulse (pre-registration)

Decision timestamp precedes any Phase102 PnL inspection.

## Hypothesis
Cross-sectional 24h expansion/contraction in USD-M open-interest value may carry a native participation impulse independent of price and taker-flow transforms. Test the simplest fixed continuation hypothesis: rank robustly by 24h log change in `sum_open_interest_value`, lag the feature one full hour (`t-1`), squash with unit `tanh`, L1-normalize, and allocate fixed gross 0.20.

## Locked specification
- Source: official Binance USD-M daily metrics archives already train-audited in Phase63.
- Feature: `log(sum_open_interest_value_t) - log(sum_open_interest_value_{t-24h})`, then `.shift(1)` before target formation.
- Cross-section: hourly median/MAD robust z-score; require >=10 simultaneous valid assets and positive MAD.
- Direction: continuation (`+z_oi`), fixed before PnL.
- Transform: `tanh(z_oi)` with unit scale; L1 normalization; gross 0.20.
- First gate: severe transaction costs on chronological TRAIN only, using existing temporal-fold/stability diagnostic.
- Missing archives remain missing; no fill from later observations.
- Single hypothesis only: no parameter grid, sign flip, rescue, threshold search, or post-result retuning.
- Holdout MUST NOT be listed, parsed, loaded, inspected, or optimized on in this gate.
- V16 Frozen and V99 Frozen are immutable.

## Decision rule
PASS only if the existing `stable_train` diagnostic passes. A PASS freezes this exact specification for supersevere costs, regime matrix, benchmark envelope and reproducibility before any untouched-holdout gate. FAIL is permanent for this specification and triggers a distinct pre-registered hypothesis, not a rescue mutation.
