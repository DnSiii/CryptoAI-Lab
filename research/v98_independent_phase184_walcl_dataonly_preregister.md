# V98 Independent — Phase184 WALCL DATA_ONLY preregistration

Status: **PREREGISTERED / DATA_ONLY / NO PNL**

## Scientific rationale

Phase183 closed on source accessibility without observing MOVE values. Phase184 moves to a genuinely distinct macro-liquidity stock observable: Federal Reserve total assets (`WALCL`, Assets: Total Assets: Total Assets (Less Eliminations from Consolidation), Wednesday level). This tests central-bank balance-sheet liquidity rather than equity/rates implied volatility, yields/curve, breakeven inflation, financial-stress indices, HY spread, DXY, WTI, TGA, or RRP.

## Frozen scope before acquisition

- Observable: FRED series `WALCL` only; no alternate balance-sheet series.
- Source: Federal Reserve Bank of St. Louis FRED CSV endpoint only. No source shopping.
- Research period: 2023-01-01 through 2025-12-31 only.
- Native weekly cadence is preserved; no interpolation or synthetic daily filling.
- DATA_ONLY: no crypto positions, returns, labels, thresholds, PnL, validation, or final holdout may be read or computed.
- Acquisition must be repeated twice independently; normalized observation SHA-256 must match.
- Required checks: source/series identity, first/last usable date, yearly counts, missing/nonfinite values, duplicate dates, monotonic dates, maximum calendar gap, descriptive quantiles, and causal/publication availability.
- Conservative causal policy for any later experiment: a Wednesday WALCL observation cannot affect crypto exposure until the next UTC day; same-day use is forbidden. A later economic preregistration must additionally respect any documented FRED release timing if it implies a later availability boundary.

## Pass/fail gate

`PASS_DATA_ONLY` requires all of: exact `WALCL` identity; non-empty 2023/2024/2025 coverage; >=50 usable native weekly observations in each complete year; monotonic unique dates; no parsed missing/nonfinite values; maximum calendar gap <=10 days; duplicate acquisition hashes identical; no access to dates >=2026-01-01; no V16/V99 use.

If provenance/access/coverage/integrity fails, decision is `REJECT_DATA_AVAILABILITY_NO_RESCUE`. No alternate-source shopping, interpolation, backfill, threshold search, economic test, or rescue is allowed.

If and only if DATA_ONLY passes, a later phase may preregister exactly one fixed training-only economic transformation before any PnL is observed. Phase184 itself cannot select a lookback, threshold, sign, or sizing rule.