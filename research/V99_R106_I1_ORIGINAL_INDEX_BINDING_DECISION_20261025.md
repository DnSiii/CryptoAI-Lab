# V99 I1 — original same-update underlying-index binding decision (2026-10-25 05:49 BRT)

**SOURCE_ONLY/HOLD — NO PROMOTION.** This is a first-party *exchange-published index field in original captured ticker messages*, not a historical underlying fill, full options lifecycle, return, margin certificate, or trading authorization.

## Real execution and independent verification

- Preregistered exact capture-key join **before implementation** in commit `d17b445`, then implemented in `research/tools/v99_r106_i1_original_index_binding.py` with independent raw-gzip reexecution in `research/verification/independent_v99_r106_i1_index_binding_oracle.py`.
- Recovered the **same** original Tardis Deribit ticker minute gzip archive (Actions 40170453274), first-party Deribit historical instrument registry (40148052668), and previous independently audited original 46-pair unit-credit report (40174287180). Replayed the original compressed receipts, bound each option book to its **exact original symbol + local arrival microsecond + exchange microsecond**, verified original book bid/ask and sizes and every source digest. No interpolation or later quote.
- [GitHub Actions 40178076296](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40178076296) **SUCCESS**. Independent raw-byte oracle reproduced all fields and counts. Forged index value was correctly rejected.
- Compare from prior branch head `4b195b13` to `e536a5f`: exactly four **new** prereg/code/oracle/workflow files; no Frozen, paper/results, champion, validation, holdout, dashboard performance or order code changed.

## Original source observations (not returns)

- **50/50** original eligible option books have an exchange-published `index_price` in the exact same raw ticker update.
- **46/46** previously audited adjacent-strike put-vertical quote pairs have both legs' original `index_price`.
- Only **23/46** pairs have **exactly equal** underlying index prices across the two independently timed option updates. The remaining **23/46** have different index values. This is **not** evidence that half the spreads were impossible to trade; it is proof that pairing last-known quotes does **not** produce an identical-time, identical-underlying snapshot. Neither these pairs nor the 31/46 severe and 21/46 supersevere previously positive *unit credits* establish two-leg fills, native size-aware feasibility, profitability or economic edge. Do not use this post-observation discrepancy as a tuned strategy filter or winner selection.
- The source bridge now exposes the original underlying reference per leg without inventing spot execution. This removes one internal missing-input ambiguity, **not** the external complete-archive block.

## Exact blocking dependencies and next critical step

**0/182 original complete entry-through-exit certified asset-week lifecycles**, **4/182** asset-weeks with original sampled entry two-strike books. Need an authenticated, licensed **2021-12-09 to 2023-09-30** BTC/ETH Deribit two-sided bid/ask+size archive with venue and local arrival timestamps, complete 91 decision Sundays and all 21–45d holding/exit periods, gap manifest and source entitlement; original lot/quote-size unit conversion, historical account fee tier and settlement charges, coin margin/liquidation rules, and independently reexecuted full self-financing portfolio accounting. Prior non-sample archive request returned HTTP 403 without entitlement. Alternative: a different licensed venue/vendor archive with equivalent historical coverage and audit evidence; no source substitution by daily DVOL or synthetic fills.

**Next internal work:** use the now-proven exact original index reference to build a *conservative native-unit/size-aware execution interface*, failing closed when lot-unit, fee/margin or full lifecycle receipts are missing. Do not claim a complete historical TRAIN until five chronological folds, 3x2 regimes, severe/supersevere cost, tails, benchmark and independent accounting gates are executed on complete original inputs. Validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 remain sealed. No orders or ROI claimed.
