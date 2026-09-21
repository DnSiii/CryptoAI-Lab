# V99 R106 Phase97 — top-trader size divergence TRAIN-ONLY preregistration

## Status
Pre-registered before any Phase97 return/PnL evaluation. Phase96 is permanently rejected. Phase97 is a distinct participant-composition hypothesis: it uses the divergence between top-trader position-weighted and account-count long/short ratios, not taker flow, open interest, or a sign flip of a rejected signal.

## Hypothesis
When the position-weighted top-trader long/short ratio is high relative to the account-count top-trader ratio, larger top-trader positions are relatively more long than the top-trader headcount. Treat this size-vs-headcount divergence as informed positioning and test cross-sectional continuation.

## Frozen specification
- Source: official Binance USD-M daily metrics archives, train period only; SHA256 CHECKSUM + ZIP CRC required.
- Fields: `sum_toptrader_long_short_ratio` and `count_toptrader_long_short_ratio`, both positive finite.
- Feature: `log(sum_toptrader_long_short_ratio) - log(count_toptrader_long_short_ratio)`.
- Causality: shift the hourly feature by exactly t-1 before constructing weights.
- Cross-section: simultaneous median/MAD robust z-score; require >=10 assets and non-degenerate MAD.
- Signal: `raw = +tanh(z)` (continuation), fixed unit tanh scale; L1 normalize cross-sectionally.
- Alpha gross: 0.20.
- Costs: severe cost gate first.
- Selection: chronological train only through the existing train_end; four temporal folds and canonical stable_train diagnostic.
- Missing archives are never filled; no grid, threshold sweep, sign flip, rescue, or post-result retuning.
- Holdout must not be listed, parsed, inspected, or optimized.
- V16 Frozen and V99 Frozen must remain byte-identical.

## Decision rule
PASS only if the existing canonical `stable_train` gate passes. On PASS freeze this exact specification and proceed to supersevere, regime matrix, benchmark envelope and reproducibility before untouched holdout. On FAIL permanently reject Phase97 and move to a genuinely distinct pre-registered family.