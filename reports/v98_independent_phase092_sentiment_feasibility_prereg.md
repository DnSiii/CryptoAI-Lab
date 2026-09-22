# V98 Independent Phase092 — Exogenous market-sentiment feasibility preregistration

Status: **PREREGISTERED / DATA FEASIBILITY ONLY / NO ALPHA PNL**.

## Independent information class

Phase092 tests only whether a reproducible exogenous crypto-market sentiment series exists. This is distinct from the exhausted price/volume/volatility/funding/OI/order-flow/basis/calendar/cross-venue families because the observation is a published sentiment index rather than a transformation of canonical trading fields.

## Frozen source and field

Source is fixed before inspection: Alternative.me public Crypto Fear & Greed API, endpoint `https://api.alternative.me/fng/?limit=0&format=json`. Retain only the published daily `value` and its Unix `timestamp`; `value_classification` is metadata only and may not become an alternate feature. No alternate provider/source rescue is allowed inside Phase092.

## Fixed feasibility interval and gates

Required interval: 2023-01-01 through 2025-12-31 UTC. PASS_DATA_ONLY requires: (1) >=99.0% expected daily coverage over the full interval; (2) duplicate timestamps <0.1%; (3) no unexplained gap >3 calendar days; (4) every retained value is finite integer 0..100; (5) all retained timestamps are <=2025-12-31; (6) identical endpoint/schema is reacquirable and raw response SHA-256 is recorded; (7) no 2026 observation is used for scoring.

Any mandatory gate failure => **FAIL_DATA_NO_ALPHA**. No direction, threshold, lag, regime rule, crypto-price join or strategy PnL may be tested in Phase092.

## Isolation

Phase083 is permanently opened/ineligible and is not used. V16/V99 evidence is excluded. A PASS_DATA_ONLY result authorizes only a separately preregistered Phase093 mechanism; it does not promote a candidate or open validation/final holdout.
