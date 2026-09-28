# V99 R106 Phase169 — pre-PnL implementation audit

Date: 2026-09-28

This audit was performed before any Phase169 PnL was successfully produced.

## Scientific contract

- Phase168 dependency remains `PASS_DATA_ONLY`.
- Macro panel remains exactly `DGS2`, `DGS10`, `DTWEXBGS`, `VIXCLS`; no component was dropped after observing data or results.
- Retrieval is hard bounded to `2021-12-01 <= date < 2024-01-18`; holdout macro values are not requested.
- Five-observation impulse is computed only after dropping non-finite native observations.
- Expanding mean/std are shifted by one impulse observation, so the current impulse cannot enter its own normalization statistics.
- Hourly mapping uses the latest finite macro feature at or before `crypto UTC date - 1 day`, making same-calendar-day macro information unavailable.
- The complete hourly target is shifted one additional crypto hour before execution.
- Direction, gross cap 0.20, equal asset weights, severe cost and TRAIN gate remain unchanged from preregistration.
- No grid, sign search, horizon search, component selection, asset selection or post-PnL rescue is permitted.
- V16 Frozen and V99 Frozen remain read-only.

## Transport failure audit

Run 36397887759 failed before Phase169 PnL because FRED `DGS2` timed out after four transport attempts. Replay preparation and frozen firewall had already passed. This is classified as infrastructure failure, not alpha evidence.

The transport-only correction in commit `5544e79992fdcf9b043437ec3739848fab93543c` first requests the four preregistered series as one TRAIN-bounded FRED panel, reducing network round trips. If that transport path fails or does not return all four frozen columns, it falls back to the same four individual TRAIN-bounded FRED requests. The fallback changes neither source, values, date boundary, feature construction nor scientific gate.

## Decision discipline

The first successful Phase169 TRAIN PnL is binding. If its frozen TRAIN gate fails, this exact macro-risk-impulse mechanism is permanently rejected without retuning. If it passes, the exact specification is frozen for independent supersevere, regime, concentration, benchmark and reproducibility gates before any untouched holdout access.
