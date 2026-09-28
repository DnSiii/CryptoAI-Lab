# V99 R106 — Phase176 archive probe update

Date: 2026-09-28
Scope: DATA / INTEGRITY ONLY. No alpha/PnL/holdout access.

## Work completed

1. Re-verified the first-party OKX historical-data surface: borrowing-rate history is advertised from December 2021 onward and remains listed separately from perpetual funding (March 2022 onward). Search/indexed first-party content still does not expose the underlying borrowing archive object URLs, file names, schema, units, or exact first timestamp.
2. Implemented `scripts/v99_r106_phase176_borrow_archive_manifest.py`, a deterministic archive inspector for CSV/ZIP objects. It records SHA-256, byte size, schema, timestamp/currency identity, row count, min/max timestamp, duplicate timestamps, monotonicity, missing TRAIN months, and any row outside frozen TRAIN `[2021-12-01, 2024-01-18)`.
3. Added invariant tests covering holdout-boundary rejection, duplicate/non-monotonic timestamps, and UTC epoch-millisecond parsing.
4. Independent logic audit: the inspector does not compute alpha/PnL; any post-TRAIN row, missing TRAIN month, duplicate timestamp or non-monotonic member makes the archive gate fail closed. Ambiguous timestamp columns also raise instead of guessing.

## Decision

**SOURCE REMAINS NOT ADMITTED FOR ALPHA.** The tooling required to inspect actual files is now reproducible and committed, but the actual OKX borrowing-rate archive objects have not yet been exposed through the accessible first-party page/search surface. Documentation-level `December 2021 onward` is still insufficient evidence for exact boundary, uninterrupted fold coverage, schema/units, and publication semantics.

Do not substitute account statements, current API observations, scraped third-party mirrors, shortened TRAIN, interpolation, favorable currency selection, or any holdout-period data.

## Next deterministic action

Obtain the first-party downloadable borrowing-rate archive objects for frozen TRAIN only; run the committed manifest tool; persist the resulting manifest plus raw-object hashes. If archive coverage passes, separately establish publication semantics/t-1 before preregistering any alpha. If files cannot be reproducibly obtained or coverage fails, reject this source pre-PnL and move to the next orthogonal source family.

V16 Frozen and V99 Frozen remain read-only and untouched; holdout remains untouched.
