# V99 I1 — fixed original-quote native fee-cap envelope (2026-10-25; preregistered before calculation)

**SOURCE_ONLY / HOLD / NO PROMOTION.** This is an accounting dependency check, NOT a new strategy, actual account fee, fill, profit, NAV, or economic TRAIN. Preserve the original 46 adjacent put pairs, without filtering, optimizing, or selecting a winner. Validation and final holdout remain sealed.

## Ex-ante arithmetic and sources
Read the unchanged original source credit artifact from Actions 40174287180 and the original expiry-index terminal artifact from Actions 40185981946. Verify their SHA-256 bindings, every pair key, original bid/ask premium and per-leg expiry intrinsic. Independently re-execute the same arithmetic without importing the primary fee calculator. Reject altered source bytes, false historical certification, and unauthorized promotion.

For one **assumed source unit only** (not authenticated native contract size/lot), compute two explicitly *illustrative* dated published fee examples, with Decimal and per-leg cap:
- `published_2019_example`: option entry fee `min(0.0004, 0.20 * option premium)` coin/leg; expiry delivery fee `min(0.0002, 0.20 * intrinsic coin)` coin/leg. Historical public source: Deribit's 2019 general user information at https://medium.com/@Deribit/deribit-general-user-information-8d7d0235b68a .
- `current_2026_example`: entry `min(0.0003, 0.125 * premium)`; delivery `min(0.00015, 0.125 * intrinsic coin)` per leg. Current source: https://support.deribit.com/hc/en-us/articles/25944746248989-Fees .

For the short put use its **bid** as opening premium, long put its **ask**; expiry intrinsic for each put is `max(strike - original delivery index,0)/original delivery index`. Fees are nonnegative and summed over both legs, with no combo discount assumed. Report only illustrative coin fees, fee-cap hits and historical account fee status; **do not** recompute ROI, change severe/supersevere scenarios, change any entry decision, or claim either schedule applied during 2021–2023. Both public examples are NOT dated evidence of the actual historical tier on every TRAIN decision, and actual native quantity and liquidation remain unverified.

## Fixed gate
Output `historical_fee_tier_certified=false`, `native_contract_quantity_certified=false`, `economic_train_run=false`, `orders_enabled=false`, `validation_opened=false`, `holdout_opened=false`, `promotion_authorized=false`. Actual historical 2021–2023 fee schedule (effective dates, option cap, delivery fee, account tier) must be obtained before economic certification; public current fee page alone is not a substitute. This implementation removes a missing *calculation*, not a missing *historical evidence source*.
