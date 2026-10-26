# V99 I1 post-entry native maintenance correction — actual CI decision, 2026-10-26 03:47 BRT

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION. No economic TRAIN, no historical ROI, no orders, no validation or holdout opened.** C1 remains permanently rejected. V16/V99 Frozen, legacy champion, paper/results and dashboard performance are unchanged.

## Defect reproduced and fixed
- Existing `open_vertical` could pass initial native cash/reserve despite the original entry book already showing an immediate two-leg mark-to-close liability large enough to breach maintenance. This is an **accounting/solvency false positive**, not a profitable strategy.
- Preregistered correction in `V99_R106_I1_POST_ENTRY_MAINTENANCE_LOWER_BOUND_PREREG_20261026.md` **before implementation**.
- Native replay now rejects opening when `cash_after_premium - existing_mark_liabilities - max(0,qty*(short_ask-long_bid)) < existing_maintenance + new_maintenance`. Exit fees/slippage are **not** included in the bound; passing remains only a necessary safety check, never an executable fill or certified margin.
- Overlapping opens now require the new original as-of index to match the existing marked positions' index exactly. No change to fixed Monday entry, tenor, strategy selection, source-clock/quote-age or liquidity gates.
- Independent Decimal reference journal recomputes the post-entry maintenance bound without importing production accounting. Added adversarial controls for insufficient post-entry NAV even when cash covers reserve, and independently forged overlapping index.

## Executed verification (not claimed historical economics)
- Production, independent oracle and tests committed on research branch; final source SHA **`23c6c4ae46143c4aa6b90ff523fed7cb20e2f2dd`**.
- [GitHub Actions 40281857535](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40281857535): **completed SUCCESS**, **14/14 deterministic synthetic tests passed**.
- Both severe and supersevere synthetic **8-event / 2-position / 1-NAV** journals independently matched; forged maintenance and index counterexamples rejected.
- Intermediate workflow runs at partial commits may fail; the final commit and job logs above are the reference. No CI status is treated as trading validation.

## External blocking evidence / next genuine step
- Original legally licensed Deribit BTC **and** ETH options BBO+sizes, arrival+venue clocks and complete entry/mark/exit/settlement lifecycles for TRAIN 2021-12-09..2023-09-30, including instrument/lot conversions, gap manifest and source hashes. Original sampled entry books cover **4/182 asset-weeks**; **0/182 certified full lifecycles**.
- Historical account-specific maker/taker/delivery fees, original delivery index receipts, initial/maintenance/liquidation margin schedule, and native collateral requirements.
- Alternatives: an independently verified full-history Tardis entitlement, CoinAPI or Amberdata licensed archive meeting **all** original fields and continuity, plus venue dated native terms. A key or synthetic CI alone is insufficient.
- Once complete licensed evidence exists, bind this ledger to original complete lifecycle data; preregister one distinct integrated I1 architecture, execute five chronological TRAIN folds, six regimes, severe/supersevere cost/tail/DD/benchmark envelope, and independent economic replay/gates. Do **not** open validation [2023-10-01,2024-01-18) or holdout >=2024-01-18 without passing TRAIN and freezing the candidate.

**No promotion, no claimed PnL, no real orders, no Frozen/paper/champion mutation.**
