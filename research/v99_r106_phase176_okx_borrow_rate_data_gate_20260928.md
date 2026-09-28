# V99 R106 — Phase176 OKX borrowing-rate source gate

Date: 2026-09-28
Scope: DATA / INTEGRITY ONLY. No alpha, PnL, sign, threshold, weight, asset subset, leverage or holdout inspection is authorized.

## Prior scientific boundary

Phase175 admitted OKX borrowing-rate history only as a candidate and required a deterministic source gate before any alpha specification. This phase executes that gate at the source/documentation level.

## Independent source verification

First-party OKX Historical Market Data currently states:

- tick-level trade history: September 2021 onward;
- perpetual funding history: March 2022 onward;
- high-resolution L2 order book: March 2023 onward;
- **historical borrowing rates: December 2021 onward**.

This establishes that borrowing rate is presented by OKX as a distinct historical market-data object rather than perpetual funding or an account statement. It also establishes source-level temporal plausibility for the frozen TRAIN start (2021-12-01), but NOT exact timestamp completeness.

Canonical first-party page checked: https://www.okx.com/en-sg/historical-data

## Gate results

1. Market-wide historical-data classification: PASS at documentation level.
2. Distinct from perpetual funding: PASS at documentation level; OKX lists separate objects with different start dates.
3. Earliest month compatible with TRAIN start: PASS provisionally (December 2021), but exact 2021-12-01 timestamp is NOT YET PROVEN.
4. Exact per-currency timestamps / schema / units: NOT YET PROVEN.
5. Full uninterrupted coverage through 2024-01-18: NOT YET PROVEN.
6. Monthly gap map: NOT YET PROVEN.
7. Deterministic raw hashes / immutable snapshot: NOT YET PROVEN.
8. Causal publication semantics sufficient for t-1: NOT YET PROVEN.
9. Frozen temporal-fold coverage: NOT YET PROVEN.

## Decision

**NOT ADMITTED FOR ALPHA YET.** Documentation verification materially advances the candidate, but the remaining requirements require inspection of the actual downloadable archive files. No formula or PnL may be created until the archive-level gate passes.

This is deliberately fail-closed: the phrase “from December 2021 onward” is not treated as proof that observations exist at the exact frozen TRAIN boundary or that every required month/currency is complete.

## Next deterministic work unit

Acquire only TRAIN-eligible OKX borrowing-rate archive objects, without requesting observations after 2024-01-18. Produce a machine-readable manifest containing source URL/object name, byte size, SHA-256, min/max timestamp, row count, schema, currency/instrument identity, missing-month map, duplicate timestamps and timestamp monotonicity. Then evaluate predefined temporal-fold coverage before any alpha preregistration.

If the archive interface cannot expose reproducible files or the frozen TRAIN coverage is materially incomplete, reject the source pre-PnL rather than shorten TRAIN, alter folds, choose favorable currencies, interpolate structural gaps, or use holdout observations.

## Invariants

- causal t-1 remains mandatory;
- chronological TRAIN-only selection remains mandatory;
- holdout remains untouched;
- severe/supersevere costs, regime matrix, benchmark envelope and reproducibility remain mandatory for any later alpha;
- no rescue tuning or source cherry-picking;
- V16 Frozen and V99 Frozen remain read-only and untouched.
