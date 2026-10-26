# V99 I1 — original arrival-day source parser correction: executed result (2026-10-26 19:49 BRT)

**SOURCE_ONLY/HOLD — NO PROMOTION. No economic TRAIN.** This repairs a source-ingestion correctness defect, not an alpha model or a certified original trade lifecycle.

## Preregistration, implementation and independent checks
- Protocol fixed **before code**: `research/V99_R106_I1_ORIGINAL_ARRIVAL_DAY_PARSER_CORRECTION_PREREG_20261026.md`, commit `d313260`.
- Fixed `research_tools/v99_r106_tardis_full_day_source.py`, commit `80ad6fc`: Tardis groups original CSV by **local arrival day**. Previously an exchange event timestamp from just before midnight could incorrectly veto a legitimate current-day arrival. New gate checks local arrival day, event <= arrival, nonnegative event and monotonic local capture order. Corrected malformed decimal-strike regex. A source quote older than the preregistered 10-second event-to-arrival bound is counted as stale, not a fresh two-sided executable quote. These are source checks, not proof of fill availability.
- Added four falsification tests, commit `8f454b7`: prior-day event/current-day arrival, decimal strike, stale event not establishing quote coverage, malformed option instrument.
- [GitHub Actions 40415252135](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40415252135): **SUCCESS** on `8f454b7`; **15/15 synthetic tests passed**; actual read-only source step `BLOCKED_NO_AUTHENTICATED_ENTITLEMENT`, **network_requests=0**. No original non-sample day downloaded and no historical option lifecycles certified.
- Independent GitHub compare from prior head `3d92a0f` to `8f454b7`: exactly 3 changed paths (prereg, parser, adversarial tests); no Frozen V16/V99, paper/results, champion, dashboard, validation or holdout changes.
- Vendor documentation: https://docs.tardis.dev/downloadable-csv-files/api — daily files partitioned by `local_timestamp`. A green CI only verifies software invariants, not archive entitlement.

## Remaining external critical-path block
The Actions secret `TARDIS_API_KEY` is still missing. Need written licensed full-date Deribit BTC+ETH OPTIONS historical entitlement for 2021-12-09..2023-09-30, authenticated full 21–45-day BBO+size entry/mark/exit tapes with original event and arrival clocks and gap manifest, plus historical native fee/delivery/lot, original delivery index and dated margin/liquidation receipts. Alternative: independently equivalent licensed Amberdata/CoinAPI archive with verified coverage, rights, clocks, sizes and continuity. No raw paid data may be published.

**Decision:** `SOURCE_ONLY/HOLD`, **0/182 certified complete lifecycles**, 0 original authenticated requests this run, no historical integrated five-fold severe/supersevere economic TRAIN, no ROI, no orders, no promotion. Next: authenticated full original tape and dated native terms, then complete independent economic replay and gates; preserve sealed validation and final holdout.
