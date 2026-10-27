# V99 I1 — fixed 28–35d option tenor vs sealed TRAIN boundary: causal cash classification (preregistered 2026-10-27)

**SOURCE_ONLY/HOLD — NO PROMOTION.** This is a deterministic accounting/denominator correction, **not** a parameter change, strategy optimization, model selection or economic TRAIN. No original option archive, fills, historical fees/margins, validation or holdout will be accessed.

## Discovered discrepancy and frozen arithmetic
- Original signal schedule: **91** maturity-eligible Mondays per asset based on **21d** minimum; **182** original-source causal signal decisions (BTC + ETH).
- The separately preregistered I1 fixed put-vertical **requires 28–35d** to contractual expiry, and the Quote contract gate requires expiry strictly **before 2023-10-01T00:00Z**. Thus a Monday is structurally eligible only if decision_ms + 28*86400000 < TRAIN_END_MS.
- **2023-09-04 00:00 UTC** is 27 calendar days before sealed TRAIN end, so it is **necessarily CASH** under the existing rule for BOTH assets, independent of market quotes or positive signals. **2023-08-28** is still potentially eligible (34 days). The fixed rule yields **90 potentially eligible Mondays/asset = 180 potential asset-weeks**, **2 structurally right-censored asset-weeks**. The 91/182 original signal schedule must remain unchanged and must never be relabeled as 180 observed trades, full lifecycles, or profitable folds.
- This is an **ex ante time/contract feasibility identity**, not a retrospective PnL-based filter. The original signal, fold boundaries, fixed moneyness, tenor, fee scenarios, margin and all source gates stay unchanged.

## Implementation and falsification protocol
1. Keep validating the complete causal signal row and all supplied quote rows. Never suppress invalid or future original quotes merely because the decision is censored.
2. For a valid source-empty 2023-09-04 decision, primary fixture bridge must return CASH_FIXED_TENOR_RIGHT_CENSORED with unchanged economic wallet and advanced causal decision clock, instead of generic source/signal cash. This classification is **only** for structural impossibility, not an inference about historical missing data.
3. Separate independently implemented oracle must calculate the same date inequality without importing primary selector, accept the special cash only when 28d cannot fit before sealed end, reject forged special cash on earlier dates, reject generic cash on the censored date, and never accept a profitable trade there.
4. Test both severe and supersevere, positive and no-premium signals, preceding potentially eligible 2023-08-28, and forged decisions. Trigger actual GitHub CI, inspect logs and file diff; no economic/paper/holdout promotion.
5. Preserve immutable V16 Frozen, V99 Frozen, paper-results, legacy champion and sealed validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18.

**Remaining genuine external blocker:** licensed original 2021-12-09..2023-09-30 BTC+ETH Deribit option BBO/sizes with both clocks, original complete holding/settlement lifecycles, account-specific native fees, margin/liquidation, contract units, delivery-index receipts, and independent source-to-account replay. This correction cannot certify any of them.
