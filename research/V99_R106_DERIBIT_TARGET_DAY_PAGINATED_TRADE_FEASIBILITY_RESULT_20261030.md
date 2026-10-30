# V99 R106 — 2022-01-23 first-party Deribit complete reported TRADE pagination (2026-10-30 20:54 BRT)

**Decision: ORIGINAL TRADE ACTIVITY FEASIBLE, BUT I1 QUOTE SOURCE STILL BLOCKED — NO PROMOTION / NO ROI / NO ORDERS.**

## Real original-source result and reproducibility
- [Fixed ex-ante scope](V99_R106_DERIBIT_TARGET_DAY_PAGINATED_TRADE_FEASIBILITY_PREREG_20261030.md) committed as [6d14115](https://github.com/DnSiii/CryptoAI-Lab/commit/6d141152db82f41c836ca7d8ee9fcd154ff4d373) **before** implementation and the new original API replay. Scope: **only 2022-01-23**, BTC/ETH option TRADE prints, chronological pages up to 1,000, fail-closed timestamp overlap, independent raw-byte verifier.
- [GitHub Actions 41147018078](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41147018078) **SUCCESS** as a source-only execution; 8/8 offline adversarial tests, original Deribit historical API network requests, independent reconstruction of every original JSON response, original per-page SHA256, original trade ID de-duplication, timestamp overlap and eligibility checks. Original JSON deleted before artifact publication.
- Redacted source-only artifact **13021252795**, SHA256 digest `sha256:4e6dfbcc27e5e422015c955831aeecc23a19c347629dbf8377788ad6d2105571`. Original full raw responses were ephemeral in CI, not redistributed. The independent verifier concluded `INDEPENDENT_ORIGINAL_PAGINATED_TRADE_BYTES_REPLAY_PASS`.

| Fixed original TRAIN date | Original BTC option trade prints | Original ETH option trade prints |
|---|---:|---:|
| 2022-01-23 UTC | **5,849** across **6** original API pages | **6,416** across **7** original API pages |
| 28–35-day put expiry with traded strikes | **2022-02-25, 10 distinct strikes** | **2022-02-25, 20 distinct strikes** |
| API pagination status | `has_more=false` reached with overlap verified | `has_more=false` reached with overlap verified |

**Total original prints: 12,265** for the two coins on that single historical date. This establishes that the first-party historical trade endpoint returns a fully paginated *reported trade-print result set* for the exact date and that the 33-calendar-day put expiry had historical trade activity for multiple strikes. It does **not** certify a complete market quote day, every listed option, simultaneous two-leg BBO, executable sizes, historical account fills, bid/ask slippage, margin, fees, 28–35-day I1 lifecycle or any profitability. The 2022-01-23 source check is not a strategy trial, nor evidence of 2023-10-01 onward data access.

## Critical path and limitations
- **658/661 original BTC+ETH option quote days remain missing; 0/180 I1 complete native quote/settlement lifecycles certified.** The first-party public *trades* may independently check instrument existence and dates but **cannot be substituted for original contemporaneous executable bid/ask/size/arrival**. The historical quote vendor entitlement and full 661-day archive remain external blockers.
- Need dated written vendor grant and one authorized non-free original 2022-01-23 **BTC+ETH two-sided options quote/depth/size/arrival** sample with independent digest, 2021-12..2023-09 full coverage, and original fee/contract/settlement/margin/liquidation rules. Alternative: an independently authenticated equivalent vendor with the same coverage and usage rights. For a never-executed historical strategy, do not demand impossible realized order-fill receipts: conservative, original-quote-backed **simulated** fills are legitimate but not exchange-certified executions.
- The new source feasibility proof reduces the risk that the target 33-day expiry had no traded puts at all. It does **not** remove the paid quote archive blocker or authorize a purchase, a new strategy, a positive ROI, sealed validation or final holdout. No C1/C2/D1/D2/D3/S1/S2 retune, no Frozen V16/V99, paper/results, champion or order interface modifications.

**NO PROMOTION.** CI green means source replay and independent byte accounting passed, not a profitable engine.
