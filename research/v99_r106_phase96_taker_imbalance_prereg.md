# V99 R106 Phase96 — taker imbalance TRAIN-ONLY preregistration

## Status
Pre-registered before any Phase96 return/PnL evaluation. Phase95 is permanently rejected; this is a distinct order-flow family, not a sign flip or rescue of Phase95.

## Hypothesis
Cross-sectionally extreme aggressive taker buy/sell imbalance contains short-horizon continuation information. Use the native Binance USD-M daily metrics field `sum_taker_long_short_vol_ratio` as a contemporaneous order-flow state, then lag the feature by one hour before exposure.

## Frozen specification
- Source: official Binance USD-M daily metrics archives, train period only; SHA256 CHECKSUM + ZIP CRC required.
- Field: `sum_taker_long_short_vol_ratio`, positive finite values only; use log(ratio).
- Causality: shift the hourly feature by exactly t-1 before constructing weights.
- Cross-section: simultaneous median/MAD robust z-score; require >=10 assets and non-degenerate MAD.
- Signal: `raw = +tanh(z)` (continuation), fixed unit tanh scale; L1 normalize cross-sectionally.
- Alpha gross: 0.20.
- Costs: severe cost gate first.
- Selection: chronological train only through the existing train_end; four temporal folds and stable_train diagnostic.
- Missing archives are never filled; no grid, threshold sweep, sign flip, rescue, or post-result retuning.
- Holdout must not be listed, parsed, inspected, or optimized.
- V16 Frozen and V99 Frozen must remain byte-identical.

## Decision rule
PASS only if the existing canonical `stable_train` gate passes. On PASS freeze this exact specification and proceed to supersevere, regime matrix, benchmark envelope and reproducibility before untouched holdout. On FAIL permanently reject Phase96 and move to a genuinely distinct pre-registered family.