# V99 R106 — Phase176 borrowing-rate provenance / causality audit

Date: 2026-09-28
Scope: DATA / INTEGRITY / CAUSALITY ONLY. No alpha, PnL, threshold, sign, asset selection, or holdout access.

## New first-party evidence

OKX's official historical-data page states that borrowing-rate history exists from December 2021 onward.

However, the official API changelog establishes a materially different fact about *query availability*:

- 2025-09-02: OKX added the public batch `Get historical market data` endpoint. At launch it supported six modules: trade history, candlestick, funding rate, and order-book depths; borrowing rate was not among the documented modules.
- 2026-04-10: OKX added module `11` = `Borrowing rate` to that historical-market-data endpoint.
- 2026-08-06: OKX reduced the endpoint's maximum query range from 20 to 10 days/months depending on granularity.

Separately, older public Savings borrow-history endpoints existed before the frozen TRAIN ended, but this does not by itself prove that the present historical archive is an immutable point-in-time record, nor that historical rows expose an observation/publication timestamp distinct from later reconstruction time.

## Scientific consequence

A row labelled with a 2021-2024 observation timestamp is not sufficient evidence of causal availability at that timestamp. Because the batch archive API was introduced after the frozen TRAIN and borrowing-rate support was added to it only in 2026, the current archive may be a retrospective export of earlier observations. That can still be valid research data **only if** its semantics establish that each value was determined/published contemporaneously and could not have been revised using future information.

Therefore the source cannot pass the causal t-1 gate merely from date coverage or hashes.

## Phase176 decision

**SOURCE REMAINS NOT ADMITTED FOR ALPHA/PnL.**

Admission now requires all of the following, fail-closed:

1. complete frozen-TRAIN coverage `[2021-12-01, 2024-01-18)` from first-party objects;
2. deterministic hashes/schema/identity/ordering/overlap checks from the hardened manifest;
3. explicit field semantics and units;
4. evidence that each rate is an observation fixed or published at/after its row timestamp, not a hindsight reconstruction/revision;
5. a conservative availability rule that permits an additional t-1 lag without using future rows;
6. no post-TRAIN row used for selection, calibration, normalization, sign choice, or validation.

If item 4 cannot be established from first-party documentation or archive metadata, Phase176 is rejected for causal alpha research even if coverage is complete.

## Independent anti-overfit conclusion

Do not infer an edge from the existence of a long archive. Do not substitute current API accessibility for historical information availability. Do not tune around missing months, currencies, or publication ambiguity. Do not inspect PnL until the DATA and CAUSALITY gates both pass.

V16 Frozen and V99 Frozen remain untouched. Holdout remains untouched.
