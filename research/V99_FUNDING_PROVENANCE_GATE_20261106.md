# V99 funding provenance gate — 2026-11-06 (read-only evidence)

## Raw manifest evidence
Read `paper-results/reports/paper_data_sync_v13.json` at blob `32706f1e8c8f698c47f06ced494f4ef039239103`.
- generated_at_utc: `2026-11-07T00:38:17.724677+00:00`.
- expected_latest_closed_hour: `2026-11-06T23:00:00+00:00`; publication_lag_hours: `0`.
- maximum_funding_lag_hours: `12`.
- `FTMUSDT`: funding_lag_hours `12135` (over limit by `12123` hours).
- `MKRUSDT`: funding_lag_hours `10191` (over limit by `10179` hours).
- Most remaining symbols: 7 hours; KAVA/ONT/AXS/ZIL/ENJ: 3 hours.
- The sampled ADA record shows no new klines/funding rows and points to a public Binance REST funding source. A zero publication lag for klines does NOT imply current settled funding for every instrument.

## Decision / operational gate
**NO PROMOTION.** Neither FTM nor MKR is eligible for a *new exchange-proven economic certification* from this manifest. Do not substitute zero funding, forward-fill missing settlements, or silently mark them fresh. These may be inactive/delisted symbols; this is a hypothesis, not verified from the manifest alone.

Before running a new candidate, map each proposed traded instrument to original exchange settlement/fill receipts for the actual timestamp and native fee tier; record symbol lifecycle, exchange contract identity and coverage. Reject or quarantine a candidate that requires an unproven interval. An ex-ante exclusion rule for unsupported instruments must be registered **before** candidate evaluation, never chosen after inspecting PnL. Preserve immutable Frozen and historical ledgers, including existing old observations. Do not modify paper-results to cosmetically repair timestamps.

## Publication audit
`gh-pages/dashboard/v99_research.js` reads canonical `paper-results/dashboard/dashboard_data.json`, checks market timestamp, displays `RESEARCH ONLY` and age, and fails closed when canonical fetch fails. The timestamp freshness check is market-level, **not** a per-symbol funding certification. Browser-served data and funding economics still require independent verification.

## Next shortest path
1. Verify the original Binance symbol lifecycle and funding receipt coverage for FTM/MKR; distinguish expected delisting from collector defect, using exchange originals rather than synthetic interpolation.
2. Establish strict instrument-level provenance gate for *new* TRAIN-only research; use existing full-history first-party sources for eligible instruments, and keep validation [2023-10-01,2024-01-18) sealed and final holdout >=2024-01-18 unopened.
3. Run a genuinely distinct pre-registered complete architecture only after complete fees/funding/fills evidence; independent portfolio accounting and five chronological folds under severe/supersevere costs are mandatory. C1 and D1 remain rejected.
4. I1 options branch is blocked by unreceived/unlicensed full Deribit historical options coverage (~658 of 661 required days missing). Require explicit commercial license/permission and authenticated complete original history; no purchase without approval.

No orders, ROI claim, historical rewrite, frozen mutation or economic execution was performed in this audit.
