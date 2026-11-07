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

## Follow-up 2026-11-07 01:38 UTC — independent read-only cross-check

Source: `paper-results/reports/paper_data_sync_v13.json`, blob `4753a6365cfe1729c775ab7d495f00378c9c4606`, and `paper-results/state/paper_v13_state.json`, blob `ac654da5e085cb0e70e3a1ab935c99869dafc3e1`.

- Market candle boundary now `2026-11-07T00:00:00Z`, with `publication_lag_hours=0`; V13 state `latest_data_timestamp` agrees, `new_forward_hours=2045`, `mode=PAPER_ONLY`, `real_orders_enabled=false`.
- FTM funding lag increased to **12136 h**, MKR to **10192 h**, while BTC/ETH funding lag is **8 h** and remains within the configured **12 h** threshold. V13 state explicitly quarantines `FTMUSDT` and `MKRUSDT`. The stale funding is not proof of a collector defect or delisting by itself.
- Additional independent discrepancy: `EOSUSDT` kline `latest=2025-05-21T09:00:00Z`, `rows_added=0`, despite its funding `latest=2026-11-06T16:00:00Z`. The global funding-lag map omits EOS. This is a **cross-feed lifecycle mismatch**, not evidence of a currently tradable EOS perpetual. Do not infer tradability from one fresh feed alone. Confirm exchange contract identity and symbol status from original exchange metadata before any new strategy includes EOS.
- GitHub Actions run `42313431356` completed successfully; its paper job includes `Verify paper safety and freshness`, `Verify published history was not rewritten`, and `Publish durable paper results`, all successful. This validates workflow gates, not economic PnL or browser rendering.

**Decision:** NO PROMOTION. Keep the existing V13 paper and immutable historical records untouched. For any *new* TRAIN candidate, require a joint instrument identity + contemporaneous kline + actual settled funding + fee/fill provenance gate. A global `publication_lag_hours=0` is insufficient to certify individual instruments. Next engineering action is a fail-closed, instrument-level coverage validator with independent tests on real receipts; do not filter assets posthoc based on returns. No new strategy run or order was performed in this follow-up.
