# V99 I1 — licensed one-day transfer completeness preflight (preregistered 2026-10-29, before code change)

## Observed reproducible integration defect (read-only code audit)
`research.tools.v99_r106_i1_tardis_licensed_transfer._validate_gzip` currently calls `scan_day` but discards its hourly coverage result. Consequently, a vendor response with only one valid BTC and ETH put quote (or any number concentrated in one hour) is published as a completed original day by `transfer`. The later 661-day nonfixture importer requires **24/24 original arrival hours for BOTH assets**, so the acquisition pipeline can falsely count a partial day as downloaded and then refuse to finish the complete TRAIN after all 661 transfers. This is an internal integration blocker, not a market signal or a strategy result.

## Fixed repair and adversarial acceptance before implementation
1. Apply the **already-existing** `require_hourly_original_coverage(scan_day(path, day))` contract inside the licensed-transfer validation path, for both downloaded and preexisting files, BEFORE atomic publish or skip. Do not change the original 24-hour definition, CSV parsing, chronology, symbol criteria, cost, strategy, five TRAIN folds or historical partitions.
2. Update the **offline mock vendor fixture** to contain valid BTC/ETH original-shaped puts in every UTC hour of its one day. Test a complete 24/24 day transfers and is resumable; test a 23/24 or 1/24 source is refused with no published final file, and an existing incomplete original is refused without overwrite.
3. Execute the existing local-original-tape-preflight GitHub workflow on the research branch, poll actual run, inspect results. The existing real-source check MUST still print `BLOCKED_ORIGINAL_LICENSED_661_DAY_OPTIONS_ARCHIVE_MISSING` if the external licensed tape is absent. No invented market data, ROI, native fee certification or orders.

## Decision boundary
This is an acquisition safety repair that prevents a *false complete-day receipt*; it does not create a licensed archive, vendor completeness attestation, first-party historical account fee/margin/fills, or a valid I1 economic TRAIN. Preserve V16/V99 Frozen, champion, paper/results, sealed validation >=2023-10-01 and final holdout >=2024-01-18. **SOURCE_ONLY/HOLD; NO PROMOTION.**
