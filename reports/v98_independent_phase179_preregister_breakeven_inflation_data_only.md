# V98 Independent — Phase179 preregistration

Status: PREREGISTERED / DATA_ONLY

## Scientific question

Can market-implied US 10-year inflation expectations be acquired with complete training-era coverage and deterministic identity, under conservative causal timing, before any crypto PnL is inspected?

## Fixed data family

Primary series: FRED `T10YIE` — 10-Year Breakeven Inflation Rate.

Rationale: inflation expectations are economically distinct from the rejected Phase178 HY-credit feed and from Phase175/176 broad-dollar strength. This phase is data-only; no claim of predictive value is made.

## Frozen protocol

- Window: 2023-01-01 through 2025-12-31 only.
- Official FRED fredgraph CSV only; no third-party mirror/backfill.
- Require exact series field, strict chronological order, unique dates, finite positive observations, explicit missing accounting, and all observations inside the frozen window.
- Require at least 240 valid observations in each calendar year and maximum calendar gap <= 7 days.
- Acquire twice independently; normalized payload and SHA-256 must be identical.
- Same-day economic use is forbidden. Any later phase must use next-US-business-day availability or a more conservative rule.
- No interpolation from future observations.
- No crypto returns/PnL, validation, final holdout, V16, or V99 access.

## Anti-overfit locks

No economic correlation, threshold/lookback search, parameter sweep, candidate ranking, or rescue is permitted. A PASS_DATA_ONLY authorizes only a separately preregistered economic hypothesis. A data-quality failure closes the family unless the defect is demonstrably operational and repair does not change the frozen scientific gates.

Validation: CLOSED.
Final holdout: CLOSED / UNTOUCHED.
