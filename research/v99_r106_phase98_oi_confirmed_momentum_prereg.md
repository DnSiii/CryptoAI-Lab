# V99 R106 Phase98 — OI-CONFIRMED MOMENTUM (TRAIN ONLY)

## Precommitment
Phase97 was rejected with 0/4 healthy chronological folds. No sign flip, parameter search, rescue, or holdout inspection is permitted.

Phase98 tests one orthogonal interaction hypothesis: **24h price momentum is more credible when accompanied by expanding futures open interest**. This is not the inverse of any rejected Phase92–97 signal; it combines lagged market return with independently measured participation expansion.

- Native source: Binance USD-M daily metrics `sum_open_interest_value`, archives only through the existing train end.
- Integrity: each downloaded archive must pass published SHA256 and ZIP CRC; missing archives are not filled.
- Causality: OI log-change over 24 hourly observations and 24h close return are both shifted by `t-1` before portfolio construction.
- Cross-section: simultaneous median/MAD robust z-score independently for OI change and return; at least 10 assets.
- Fixed transform: `momentum = tanh(z_return)`; `confirmation = max(tanh(z_oi_change), 0)`; raw signal = momentum × confirmation; L1 normalize.
- Economic direction: continuation only when participation is expanding. OI contraction contributes zero rather than being interpreted as an opposite signal.
- Gross alpha sleeve: 0.20, fixed before PnL.
- Costs: severe cost gate first.
- Selection: chronological train only with existing temporal-fold/stable-train diagnostics.
- No grid, threshold sweep, sign flip, rescue, or adaptive scale.
- Holdout must not be listed, parsed, scored, or used for selection.
- V16 Frozen and V99 Frozen must remain byte-identical.

## Decision rule
PASS only if the existing stable-train diagnostic passes. On PASS freeze the exact specification, then evaluate supersevere costs, regime matrix, benchmark envelope and reproducibility before any untouched holdout gate. On FAIL reject permanently and move to a genuinely different hypothesis.