# V98 Independent Phase140 — T10Y2Y point-in-time revision audit

Status: **PREREGISTERED / DATA_ONLY_PIT_AUDIT**. No crypto returns, alpha or PnL may be computed.

## Purpose
Phase139 established deterministic current-vintage FRED coverage. Phase140 tests whether the exact signal horizon that a later economic candidate would use is stable across contemporaneous ALFRED vintages, rather than silently treating today's revised history as point-in-time truth.

## Frozen sources and sample
- Current reference: FRED graph CSV, series `T10Y2Y`.
- Point-in-time source: ALFRED graph CSV `T10Y2Y` with explicit `vintage_date`.
- Training years only: 2023, 2024, 2025.
- Frozen vintage sample: calendar month-end for every month from 2023-01 through 2025-12 = 36 vintages.
- For each vintage, compare only the trailing 60 calendar days, which safely contains more than the intended later 20-available-observation signal horizon.
- No alternate vintages, hand-picked dates or post-result source substitutions.

## DATA_ONLY firewall
Persist only source identity, request counts, overlap counts, mismatch counts, schema/integrity flags and cryptographic hashes. Do not persist T10Y2Y values, signs, levels, changes, descriptives, quantiles, crypto data, correlations, alpha or PnL.

## Frozen gates
`PASS_PIT_SHORTCUT` only if all 36 vintage requests:
1. return parseable CSV with first field either `DATE` or `observation_date` and second field exactly `T10Y2Y_YYYYMMDD`;
2. contain no observation dated after the requested vintage;
3. have at least 15 finite overlapping observations inside the trailing 60-calendar-day window;
4. match the current FRED normalized decimal value exactly on every overlapping observation;
5. have no malformed/duplicate accepted observations;
6. all requests complete successfully and a deterministic bundle SHA-256 is recorded.

Any mismatch closes the **current-FRED shortcut**. It does not authorize revised data for alpha; the only scientifically admissible continuation after mismatch would be a separately preregistered full ALFRED point-in-time reconstruction before any economic test.

A clean PASS authorizes a separately preregistered economic Phase141 using a conservative publication lag. It does not itself establish edge.
