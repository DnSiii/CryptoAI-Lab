# V98 Independent Phase996 — preregistered BTCUSDT 2023-02 source gap resolution

Locked before execution of Phase996 source-only reconciliation. Scope: research/v98-independent-zero, research/v98_independent/ and V98-namespaced workflow only. No V16/V99 edits, no external-engine inspection, no 2025+/holdout data, no economic parameter changes, no PnL.

## Prior authenticated observation (Phase995, run 39919774550)
- Monthly BTCUSDT markPriceKlines 1h 2023-02 archive is vendor-checksum authentic (SHA256 f15d23370f252082d8741819800b82f62ac8bbc9001b53ab6abb5d65ccb3ed3d), but has 648 rows instead of 672.
- Its only calendar hole is 2023-02-24 00:00 through 23:00 UTC, exactly 24 missing rows; the other 648 rows are identical in all 12 columns to official daily archives.
- All 28 official daily ZIPs passed their individual vendor checksums and row audits, with 672 unique valid hours, no daily faults and no download errors.
- Binance futures API responded HTTP 451; do not treat API as confirming the missing rows. Monthly-vs-daily is same vendor, two independently packaged datasets, NOT independent market-source attestation.

## Phase996 source-only hypothesis and hard gates
The 24 missing hours can be reconstructed as a **new derivative provenance-bound research artifact** from official daily BTCUSDT-1h-2023-02-24.zip without changing the vendor monthly file, Phase797 source attestor, frozen N code or any source hash.

1. Re-fetch monthly and all 28 daily ZIPs and their official .CHECKSUM files, verify SHA256, canonical single CSV member, exact 12-column schema and UTC hourly geometry.
2. Require the monthly timestamp set to equal all 672 February hours EXCEPT exactly Feb 24, 2023 UTC, no duplicates, all existing rows geometrically valid.
3. Require all 28 daily sets to have 24 unique valid hours for their dates, and all 648 monthly overlap rows to match all 12 CSV fields numerically, with timestamps exactly equal. No approximate matching.
4. Build a deterministic 672-row derivative CSV ordered by UTC, preserving all original 648 monthly rows verbatim and inserting exactly 24 checksum-verified daily rows. Emit the reconstructed CSV SHA256, source manifest with monthly and 28 daily ZIP digests, exact gap timestamps and a fail-closed decision.
5. Reject any extra mismatch, alternate gap, API-derived values, malformed schema, non-finite geometry, duplicate, missing checksum, failed request, or unverified source.
6. Do not feed this artifact to frozen Phase797 or the 90-cell economic dispatcher in Phase996. Economic reuse requires a separate, preregistered complete-engine source policy, chronological training and independent validation; do not use results to choose a source.

Success means only SOURCE_GAP_RECONSTRUCTED_DAILY_CHECKSUM_BOUND; failure means QUARANTINE. Neither authorizes PnL or promotion. Keep XRP quarantined and Phase083 holdout ineligible.
