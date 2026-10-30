# V98 Independent Phase175 — DTWEXBGS DATA_ONLY audit

Status: DATA_ONLY identity/causality audit; no crypto PnL, future-return correlation, threshold search, direction selection, or holdout inspection performed.

## Candidate identity

- Series: `DTWEXBGS` — Nominal Broad U.S. Dollar Index.
- Source: Board of Governors of the Federal Reserve System (US).
- Release: H.10 Foreign Exchange Rates.
- Units: Index Jan 2006=100, not seasonally adjusted.
- Native frequency: Daily.
- This is the broad-dollar family preregistered in Phase175; discontinued `TWEXB` is explicitly not substituted.

## Causal-availability finding

FRED exposes observation dates plus release/update metadata, but the series page does not establish a per-observation intraday publication timestamp usable for same-day crypto trading. Contemporary snapshots also show a material publication delay: e.g. the 2026-09-18 observation was updated on 2026-09-21 at 15:16 CDT. Therefore same-day use is forbidden.

For a later economic hypothesis, a causal lag must be frozen before PnL inspection and must be conservative enough to respect the H.10 publication schedule. No forward fill across unpublished observations may make a value available before its documented release.

## Integrity rules for deterministic acquisition

A Phase175 acquisition tool must:

1. request only the frozen training era 2023-01-01 through 2025-12-31;
2. preserve explicit missing observations rather than silently imputing them;
3. reject duplicate dates and non-finite numeric values;
4. record first/last valid date, valid count, missing count and annual coverage;
5. acquire twice independently and require byte/hash-equivalent normalized output;
6. persist a SHA-256 of normalized evidence;
7. never request final-holdout dates to satisfy a DATA_ONLY gate.

## Current decision

Identity and semantics PASS. Causal same-day availability FAILS and is prohibited, but the family remains eligible for DATA_ONLY because a conservative lag can be fixed before economic testing. Coverage/integrity/reacquisition still require deterministic execution before `PASS_DATA_ONLY` can be declared.

No champion is created by this audit.