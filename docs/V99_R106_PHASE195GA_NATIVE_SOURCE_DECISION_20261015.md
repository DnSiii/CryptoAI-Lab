# V99 R106 — Phase195-GA native-source continuity decision (2026-10-15 14:46 UTC)

**Decision: DATA_ONLY/HOLD. No candidate promotion, no economic replay, no Frozen/holdout change.**

## Independently checked facts
- Research branch at `98a655a1c4f19168792d26be71df62528d5436f1` when inspected.
- Durable immutable receipt branch at `2a6541d31636edd986f8da89ef8ea405a137a58c`.
- Paired durable UTC buckets: 2026-10-14T20, 2026-10-14T23, 2026-10-15T01, 2026-10-15T07, 2026-10-15T13. Inclusive interval has 18 UTC hourly buckets: **5 paired, 13 missing, zero consecutive durable pairs**. The separately archived 12:28 UTC source observation is **artifact-only**; do not backfill durable history from it.
- Official scheduled source run [38744649527](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/38744649527) and terms run [38744809092](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/38744809092) both succeeded. Their 13 UTC durable provenance refers to these run IDs and the market/terms manifest SHA256 values `136a9d9d0ad0316b21b3cc71445d0a02e26d86cb6410d5d0d8d4e31b97b57840` / `62ac7ca625437e9ebc813a2688f26fd8dbc2b1697acf6936774feafe2eb66b4c`.
- An independent read-only offline audit of the original 12:28 UTC artifact and 13:40 UTC durable observation checked 20 overlapping confirmed asset-bars with **zero revisions**, five first newly closed asset-bars, and a 12:00→13:00 UTC confirmed close transition. All five **forecast** funding notices changed; no realized position-specific funding settlements or native fee tier were attested.
- Earliest conservatively admissible causal decision from the later observed receipt: **15:00 UTC**. This is a data-timing bound, not trade authorization.
- Durable paper-results V99 Frozen snapshot read on 2026-10-15 14:46 UTC: 927 simulated forward hours through 13:00 UTC, equity multiple 0.858645 (ROI -14.1355%). This is **Frozen paper**, not R106.
- R98/R106 five-variant paper remains through 2026-10-10 05:00 UTC and its stale capped operations are quarantined; the 2026-10-15 failed five-variant refresh intentionally stopped at its epoch guard. Do not present its tracked figures as validated champions.

## Scientific next gates (preregistered)
1. Audit the entire immutable paired-source chain: strict unique-key JSON, original raw hashes, capture/run provenance, first-seen timestamps, missing UTC buckets, revisions in overlaps, exact five-asset intersection, same-hour repetition, and t-1 conservative eligibility. **No missing-hour backfill** and no use of later observations as earlier features.
2. Require at least two *consecutive durable* paired captures before declaring source continuity. Still maintain DATA_ONLY until separately proven original fee tiers, realized position-specific funding, order journal, severe/supersevere costs, train-only selection, temporal folds, regime matrix, benchmark envelope and independent reproduction.
3. Keep holdout untouched; never cross-venue-transfer Binance R106 fees/funding to OKX. Never change V16 Frozen, V99 Frozen, champion history or durable paper-results to conceal these gates.

This is a research handoff; GitHub Actions success and original-body SHA256 attest integrity of stored observations, **not** exchange-signed historical availability or positive trading PnL.
