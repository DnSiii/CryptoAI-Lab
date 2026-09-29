# V98 Independent — Phase182 VIX DATA_ONLY preregistration

Status: **PREREGISTERED / DATA_ONLY / NO PNL**

## Scientific rationale

Phase181 rejected the frozen T10YIE disinflation overlay out of sample. The next family must be orthogonal rather than a rescue of that macro-rate hypothesis. Phase182 therefore inspects direct option-implied equity volatility (`VIXCLS`) as an external risk-stress observable. This is not selected from V99/V16 and must not inspect the V98 final holdout.

## Frozen scope before acquisition

- Source: FRED series `VIXCLS` only.
- Research period audited: 2023-01-01 through 2025-12-31 only.
- DATA_ONLY: no strategy positions, returns, labels, thresholds, PnL, validation, or final holdout may be read or computed.
- Acquisition must be performed twice independently and raw normalized payload SHA-256 must match.
- Required checks: first/last usable date, yearly usable observation counts, missing values, duplicate dates, monotonic dates, maximum calendar gap, descriptive quantiles, and causal availability policy.
- Conservative causal policy for any future experiment: a daily VIX close cannot affect crypto exposure until the next UTC day; same-day use is forbidden.
- Expected business-day cadence is allowed; weekends/market holidays are not treated as data defects by themselves.

## Pass/fail gate

PASS_DATA_ONLY requires all of: non-empty 2023/2024/2025 coverage; >=200 usable observations in each complete year; monotonic unique dates; no parsed missing values; max calendar gap <=7 days; duplicate acquisition hashes identical; no access to dates >=2026-01-01; no V16/V99 use.

Any failure is `REJECT_DATA_AVAILABILITY_NO_RESCUE`. No alternative source, interpolation, backfill, threshold search, or economic experiment is allowed after a data gate failure.

If and only if DATA_ONLY passes, a later phase may preregister one fixed training-only economic transformation before any PnL is observed. Phase182 itself cannot select a lookback, threshold, sign, or sizing rule.
