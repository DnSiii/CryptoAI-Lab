# V98 Independent Phase139 — readiness / reproducibility audit

Status: **READY_FOR_REEXECUTION_AFTER_TRANSPORT_SCHEMA_FIX**. This is not a DATA_ONLY PASS and is not economic evidence.

## Independent audit
- Branch scope checked: research/v98-independent-zero.
- Frozen preregistration remains the authority for Phase139.
- Validation and final holdout were not accessed.
- V16/V99 were not used for selection or tuning.
- The first real Phase139 run (#338) failed before receiving any payload: FRED read timed out at the frozen URL. No observations, signs, descriptives, returns, correlations, alpha or PnL were exposed.
- A second parser defect was identified from the already-established FRED graph CSV contract used by prior V98 phases: the date field is `observation_date`, not `DATE`.
- These are transport/parser corrections only. Frozen series T10Y2Y, source host/path, 2023-01-01..2025-12-31 window, coverage gates, no-imputation rule, revision-detecting date+value digest, double acquisition and DATA_ONLY firewall are unchanged.
- Corrected executor v3 is persisted at `scripts/v98_independent_phase139_treasury_curve_data_only_v3.py`.
- v3 adds bounded retry/backoff (4 attempts, 90 s each) and the exact `observation_date,T10Y2Y` schema.
- No Phase139 PASS may be declared until v3 actually executes and returns PASS with identical independent-acquisition hashes/metadata.

## Decision
Phase139 remains DATA_ONLY and is authorized for reexecution after a non-economic transport/parser fix. Champion remains NONE. No Phase140 economic preregistration is authorized until Phase139 PASS is harvested.
