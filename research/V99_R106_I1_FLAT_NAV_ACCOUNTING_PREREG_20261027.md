# V99 I1 — flat-wallet terminal NAV accounting preregistration (2026-10-27 05:xx BRT, BEFORE code)

**SOURCE_ONLY/HOLD; NO PROMOTION.** This is a necessary portfolio accounting defect correction, not an alpha change, parameter retune, economic TRAIN, original execution proof, or a new phase. The fixed I1 entry strategy remains unchanged. C1/C2 rejected; sealed validation and holdout untouched.

## Defect and fixed rule

The current `account_nav(w, at_ms)` requires exactly one index among open-position marks. A valid, fully settled or cash-only wallet has zero positions/marks, so `account_nav` raises even though its native-coin NAV is deterministically the wallet cash. This prevents complete chronological fold accounting through flat intervals and after the final expiry.

Predeclare the smallest fail-closed API extension: `account_nav(w, at_ms, *, flat_index_usd=None)`. Preserve all existing open-position behavior and source-index equality. For a flat wallet, require an **explicit**, positive finite `flat_index_usd`, `at_ms == wallet.last_ms`, no positions/marks/reserve; report native NAV exactly equal to cash and USD equivalent as cash times the supplied index. Reject missing/zero/negative/nonfinite/boolean indices, and reject a supplied flat index when positions are open. This explicit input is **NOT authenticated**: actual historical USD NAV still requires an independently verified first-party index at that exact clock. Do not interpolate, fabricate, infer from options, or use future data.

Independently recompute flat NAV in the existing no-primary-import Decimal oracle, requiring an explicit event index and forbidding an index override for open-position NAV. Add both severe/supersevere flat and post-settlement tests, forged index/clock and observed USD tamper controls; run actual GitHub Actions. Existing position NAV, risk gates and no-orders remain unchanged.

**Stop gate:** code and synthetic tests may pass, but economic TRAIN remains blocked until 2021–2023 licensed original BTC/ETH BBO+sizes/arrival clocks through expiry, actual dated native fee tier/margin/lot/settlement terms and independent spot/index receipts are obtained. No ROI, validation, holdout, Frozen, paper or champion changes.
