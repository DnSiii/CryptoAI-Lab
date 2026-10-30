# V98 Independent Phase126 — Chicago Fed NFCI DATA_ONLY preregistration

Status: FROZEN BEFORE DATA VALUES / ALPHA / PNL.

## Scientific purpose
Test feasibility of a genuinely external weekly financial-conditions family using the Chicago Fed National Financial Conditions Index (FRED series `NFCI`). This phase is DATA_ONLY: it may inspect transport/schema/date coverage/integrity only. It must not print, persist, summarize, correlate, rank, plot, or otherwise inspect NFCI values, crypto returns, alpha, direction, or PnL.

## Frozen source and window
- Source: FRED CSV endpoint for series `NFCI` only; no source substitution or rescue after failure.
- Training feasibility window: 2023-01-01 through 2025-12-31 inclusive.
- Native cadence is weekly. Expected observations are the source's weekly rows inside the window; no conversion to business-day coverage.
- Validation and final holdout are forbidden.

## Frozen integrity gates
PASS_DATA_ONLY requires all of: HTTP success; required `DATE` and `NFCI` columns; at least 150 in-window weekly rows; at least 95% finite observations among in-window source rows; zero duplicate dates; strictly increasing unique dates after canonical ordering; no retained date outside 2023-2025; deterministic SHA-256 of raw payload and canonical date-only manifest.

A missing/non-finite NFCI observation counts against finite coverage but its numeric value must not be emitted. No fill, interpolation, alternate series, alternate endpoint, partial-era rescue, threshold relaxation, or source shopping is allowed.

## Isolation
No V16/V99/Phase083 evidence or files may be used. No validation/final-holdout access. No parameter search. If this feasibility gate fails, this exact source/schema family closes as FAIL_DATA_NO_ALPHA. If it passes, a later phase may preregister exactly one economic hypothesis before any alpha/PnL is opened.
