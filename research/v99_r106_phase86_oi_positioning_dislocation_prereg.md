# V99 R106 Phase86 — OI / top-trader positioning dislocation — preregistration

## Purpose
Test a mechanistically distinct native-derivatives hypothesis after Phase85 rejection: whether changes in open interest that disagree with changes in top-trader position ratio contain cross-sectional information about subsequent returns.

## Frozen hypothesis
Source fields: Binance USD-M daily metrics `sum_open_interest_value` and `sum_toptrader_long_short_ratio`.

For symbol i and hour t, require positive finite values and adjacent-hour continuity for both series. Define:

`oi_chg_t = log(OI_t / OI_t-1)`

`top_pos_chg_t = log(top_position_ratio_t / top_position_ratio_t-1)`

`raw_t = oi_chg_t * (-top_pos_chg_t)`

Trade signal is `raw_t.shift(1)` only. Positive values represent OI growth while top-trader capital positioning moves oppositely; negative values represent the converse. This is a continuous dislocation signal, not a threshold/event gate.

## Fixed evaluation
- causal t-1 only
- same train_end as the native-metrics program: 2024-01-18 00:00 UTC
- chronological train-only selection
- untouched holdout: MUST NOT be parsed, summarized or inspected
- fixed alpha gross: 0.20
- severe transaction-cost model identical to Phases61a–85
- four chronological temporal folds using the established gate
- require robust mean excluding top 1% and fold health under the established criteria
- SHA256 + CRC archive verification
- missing archives/metrics are missing; no filling
- same-hour OI/positioning pair required and adjacent-hour continuity required
- preserve existing quarantine list

## Anti-overfit prohibitions
Exactly one hypothesis. No grid, sign flip after result, threshold search, smoothing, horizon search, gross tuning, symbol cherry-picking, regime rescue or parameter rescue. If rejected, reject permanently and move to a different mechanism.

## Gate
PASS only if the existing train-alpha stability gate passes. On PASS, freeze the exact specification before supersevere costs, regime matrix, benchmark envelope and reproducibility; only after those gates may untouched holdout become eligible. On FAIL, no holdout and no retuning.

V16 Frozen and V99 Frozen are immutable.