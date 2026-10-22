# V99 R106 D1 C142 — decision-feature / journal-mark identity (2026-10-22)

**DATA_ONLY/HOLD — NO PROMOTION.** No orders, ROI, authenticated OKX receipts, validation or final holdout access. Immutable V16/V99 Frozen, paper/results and legacy champion remain untouched.

## Reproduced defect

C141 verifies that a decision is reproducible from its supplied t-1 paired OKX-labelled bars and binds the native fee tier, but does **not** bind the final feature bar to the exact t-1 spot/perpetual marks used by the C140 accounting journal. The existing synthetic C141 test fixture passes BTC last-feature perp **100.5** versus journal prior perp **101**, and ETH last-feature perp **50.25** versus journal prior perp **51**. C141 accepted and reconciled the 48-hour ledger despite the contradiction. This is an input-identity failure, not proof of any PnL.

## Local negative control and add-only C142 guard

An add-only independent wrapper now requires for **both BTC and ETH** that the final decision feature is exactly at t-1, has matching event-time availability, and equals the previous spot/perp marks actually used in the journal. It rejects missing/duplicate timestamps, nonfinite marks, partial asset sets, mismatched prices, and forged decisions; it then delegates to C141/C140 and their independent accounting. Both modeled severe/supersevere scenarios remain distinct.

**Local verification:** 12/12 new C142 negative-control tests passed, including the previously accepted C141 mismatch; 44/44 selected local D1 tests passed. All data synthetic. No historical economic TRAIN, no exchange-certified fee/funding/fill provenance, no new GitHub CI run, and no promotion.

## Next necessary steps

Publish the staged D1 C138–C142 source/test chain with the protected remote files left unchanged, execute GitHub CI, then obtain original complete historical four-leg OKX paired prices, historical account fee-tier receipts, native settlement calendars, settled funding and fill/slippage evidence. Only then execute preregistered five-fold TRAIN economics. Validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 remain sealed. The synthetic 8-hour funding cadence is a model assumption, **not exchange provenance**.
