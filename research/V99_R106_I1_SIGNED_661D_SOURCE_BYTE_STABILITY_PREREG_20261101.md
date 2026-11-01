# V99 I1 — signed replay source-byte stability gate (2026-11-01; preregistration)

## Failure mode and critical-path relevance
The signed original TRAIN bridge currently binds the original causal signal and 661-day manifest SHA-256 before and after its unsigned/signed NAV replays, but it does not recheck the 661 referenced compressed day bytes after replay. A concurrent writer could replace one gzip without changing the manifest. The source-first original-byte oracle would have checked the old tape, while a subsequently published signed report could point at changed source files. This is a real source-to-execution provenance gap, not alpha research.

## Fixed implementation
1. Parse the original manifest only after source-first oracle success; require the exact original 661 consecutive dates from 2021-12-09 through 2023-09-30, expected dated filenames, lowercase 64-character SHA-256 values and positive integer row counts. Require files to be regular and not symlinks. Verify each file SHA-256 against the original manifest both before and after signed NAV replay, in addition to the existing manifest and signal byte checks.
2. If any original daily file changes, disappears, is symlinked, or has an unexpected digest, raise a dedicated fail-closed source-mutation error before publishing any result. Do not recalculate a new manifest or accept a newly signed digest. Never read validation >=2023-10-01.
3. Test original-byte mutation during the signed replay, absence/symlink, bad manifest metadata, and successful unchanged original-day replay using synthetic files only. Trigger CI on the existing original-to-provisional workflow, and explicitly label any green test as software-only.
4. No source completeness, legal license, historical fee/funding, margin, native lot, actual fill, profitability, freeze, paper, validation, holdout, or promotion claim follows from this check.

No changes to V16/V99 Frozen, champion, paper/results, or order submission. External licensed archive remains the economic blocker.
