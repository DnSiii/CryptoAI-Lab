# V99 R106 — split-run source metadata quarantine (2026-10-16, morning BRT)

Scope: research branch only. DATA_ONLY/HOLD. V16 Frozen, V99 Frozen, sealed holdout, paper-results and champion history unchanged.

## Independent official evidence
- Scheduled market workflow run 38895514913 (2026-10-16 11:42:09 UTC): market-hourly succeeded, terms-hourly skipped. Market artifact ID 12044055586.
- Scheduled terms workflow run 38896439936 (11:50:28 UTC): terms-hourly succeeded, market-hourly skipped. Terms artifact ID 12043374638.
- These two runs share a UTC created-at hour, but are separate runs and are NOT a single atomic market-plus-terms capture. Run creation hour is not necessarily the source acquisition hour. Joining their ZIPs must never satisfy the atomic or consecutive-hour source gates.
- Scheduled same-job atomic run 38882428617 had market artifact 12037947773 and terms artifact 12038257148. Those IDs alone are metadata candidates; original ZIP SHA-256, source clocks and native t-1 still require independent attestation.
- Durable receipt branch bd31f8f485347f5d7a4c02ba51f78599dc23a4d5: 9 paired UTC buckets across 38 observed hours, 29 missing, no adjacent authenticated atomic links. These newer split runs are not additions to the durable chain.
- Official paper-results snapshot read through 2026-10-16 10:00 UTC: V99 Frozen 948 simulated hours, equity 0.849134, ROI -15.0866%. Not R106 native PnL. Archived R98/R106 comparison last timestamp remains 2026-10-10 05:00 UTC.

## Scientific decision
H_SRC_METADATA_SPLIT_01: Same UTC run-created hour does not imply same-run atomicity. A read-only research tool distinguishes distinct scheduled run IDs from one completed scheduled atomic run. A positive metadata candidate never grants source continuity, economic trials, holdout access, paper publication or champion promotion. No retroactive backfill, fee transfer, data cherry-picking or frozen modifications.

Next: run the metadata triage on official GitHub Actions metadata; independently attest original ZIPs and two adjacent acquisition hours; then prove native fee tiers and settled funding cashflows before any chronological train-only economic evaluation under temporal folds, severe/supersevere costs, regime matrix and benchmark envelope.
