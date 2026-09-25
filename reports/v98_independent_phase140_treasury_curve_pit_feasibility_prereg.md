# V98 Independent Phase140 — Treasury Curve PIT/Vintage Feasibility Preregistration

Status: PREREGISTERED / DATA_ONLY / NO ALPHA / NO PNL

## Why this gate exists

Phase139 proved that current T10Y2Y history is mechanically retrievable and reproducible over the 2023-2025 training calendar, but current FRED history is a present-day view and therefore is not sufficient by itself to prove what values were known at each historical decision date.

Official FRED/ALFRED documentation defines real-time periods and vintage dates specifically for retrieving what was known at past dates. The FRED API supports realtime_start/realtime_end and vintage_dates; API access requires a FRED API key. ALFRED's download interface also supports observations by vintage date / real-time period.

Phase140 therefore resolves revision/look-ahead risk before any Treasury-curve economic hypothesis is allowed.

## Isolation

- Branch: research/v98-independent-zero only.
- Training calendar only: 2023-01-01 through 2025-12-31.
- No V98 validation or final holdout access.
- No Phase083 selection use.
- No V16 or V99 use.
- Persisted Phase140 output must contain only data/provenance/integrity metadata, never crypto returns, PnL, correlation, signal direction, thresholds, or performance.

## Accepted PIT mechanisms

PASS requires one of the following deterministic mechanisms:

1. FRED API observations using explicit historical real-time/vintage parameters, with a valid externally supplied FRED_API_KEY; or
2. an ALFRED vintage/real-time export whose URL/request contract can be reproduced non-interactively and whose returned vintage semantics are explicitly documented.

The current non-vintage fredgraph.csv snapshot is NOT an accepted PIT mechanism.

## Frozen feasibility gates

PASS only if all hold:

1. Source identity is T10Y2Y.
2. Historical availability can be reconstructed as-of past dates, not merely current revised values.
3. For each accepted observation, a public-availability/vintage timestamp exists and is <= the timestamp at which a future economic rule would be allowed to use it.
4. No observation may be backfilled into an earlier availability date.
5. Retrieval is deterministic: two independent acquisitions of the same vintage request produce identical normalized hashes and integrity metadata.
6. 2023, 2024 and 2025 each retain >=95% usable coverage after PIT availability filtering, or the family is closed.
7. No economic direction, lookback, threshold, crypto target, return or PnL is selected or inspected in this phase.
8. Validation and final holdout remain unopened.

## Credential handling

If the only reproducible route is the official FRED API and FRED_API_KEY is absent, Phase140 status must be BLOCKED_EXTERNAL_CREDENTIAL rather than FAIL_ALPHA. Do not substitute the current revised FRED CSV and do not weaken the PIT requirement.

## Decision contract

- PASS_PIT_DATA_ONLY: permits a separate economic preregistration with one frozen causal Treasury-curve hypothesis.
- FAIL_PIT_DATA: close the Treasury-curve family.
- BLOCKED_EXTERNAL_CREDENTIAL: preserve Phase139 evidence and wait for a legitimate credential or independently verified no-key ALFRED vintage mechanism.

No PnL is authorized by this file.
