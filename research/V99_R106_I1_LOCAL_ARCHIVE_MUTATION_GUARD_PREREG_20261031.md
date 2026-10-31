# V99 R106 I1 — original daily quote scan mutation guard (2026-10-31)

**Status:** preregistered engineering integrity check only. No economic TRAIN, no ROI, no execution or promotion authorization.

## Defect and immutable scope

The 661-day local licensed-archive importer scans and validates gzip CSV records, then hashes the compressed file once after the scan. A local producer or concurrent writer can replace the original bytes between the validated read and the final hash, causing a manifest to record a different tape than the one validated. This is a source-integrity defect, not a trading signal. Scope: only `research/tools/v99_r106_i1_local_tape_import.py` and its tests; no strategy, historical prices, cost assumptions, frozen results, validation, holdout, paper or orders.

## Fixed implementation and independent test criterion

For each daily source, compute the SHA-256 of original compressed bytes **before** parsing, parse the entire gzip stream through EOF including CRC, then compute the SHA-256 **after** parsing; reject `ORIGINAL_DAY_CHANGED_DURING_SCAN:<date>` if they differ. Return the matching post-scan hash. A synthetic adversarial test must force a different post-scan digest and verify the complete import aborts without publishing any manifest. An unchanged source must continue to pass the existing full 661-day fixture and independent source oracle. Nonfixture must still require the original licensed 661-day tape, documented rights, and BTC/ETH hourly coverage.

## Limitations and gates

Two matching digests do not authenticate the vendor, contract/fee/margin schedules, fills, settlement or data completeness. A malicious writer could alter the file after the second digest; an immutable storage snapshot or a separately signed vendor manifest is still required for strong end-to-end provenance. Historical economic TRAIN, independent 5-fold validation, and promotion remain blocked pending actual licensed market bytes and native execution evidence. Keep the source-hold/no-promotion state unchanged.
