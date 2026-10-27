# V99 I1 — preregistered 28–35d lifecycle source-presence alignment (2026-10-27 16:xx BRT)

**SOURCE_ONLY/HOLD — NO PROMOTION.** This is a correction of an original-source acceptance gate, not a new alpha or PnL experiment. Existing I1 fixed-tenor entry intake accepts exactly 90 eligible Monday decisions (2021-12-13..2023-08-28), 180 BTC/ETH asset-weeks; the older daily lifecycle presence gate instead evaluates 91 Mondays and only 22 days per asset-week. A 22-day presence check cannot even serve as a necessary full-holding-period screen for a fixed 28–35d spread.

## Ex ante change (no parameter search)
- Preserve the existing legacy `V99_I1_ORIGINAL_661_DAY_TRAIN_LIFECYCLE_TAPE_V1` schema and its 91-week/22-day result unchanged.
- Add a separate opt-in fixed-tenor manifest schema `V99_I1_FIXED_28_35D_661_DAY_TRAIN_LIFECYCLE_TAPE_V1`; original archive is still **exactly 661 dated, hashed, locally ordered Deribit CSV days** strictly before 2023-10-01. Do not read validation or holdout.
- Fixed Monday eligibility: first Monday >= 2021-12-09, then every seven days while Monday + 28 days < 2023-10-01: **90** eligible Mondays, **180** asset-weeks.
- Fixed weak daily market-presence envelope: for each eligible Monday and BTC/ETH, require daily valid-put presence from Monday through `min(Monday + 35 calendar days, 2023-09-30)`, inclusive. Typical week = 36 daily presence checks; last week 2023-08-28 = 34 checks. These are NOT same-contract continuous marks, executable quotes, certified exits, or original settlement indices. Original full lifecycle still requires contract-ID-bound quotes/size, expiry settlement and native fee/margin/coin receipts.
- Report exact per-week required days, explicit scope and counts, and retain `certified_complete_option_lifecycles=0`, `economic_train_executed=false`, `promotion_authorized=false`.
- Independent oracle MUST reconstruct the calendar and daily presence from original bytes, reject forged scope/count/weekly report, and reject missing or stale daily presence. Synthetic fixture and adversarial controls only; CI success never means licensed data or economic TRAIN.
- Do not touch C1, any Frozen/paper/champion, orders, validation >=2023-10-01, holdout or dashboard claims. No retuning I1 rules.

**Real critical-path dependency unchanged:** authenticated licensed original 2021–2023 BTC/ETH Deribit option quote tape for entry and full 28–35d lifecycle, original account-specific fees/margin/liquidation/settlement terms, then independently replayed 5-fold severe/supersevere integrated economic TRAIN. A passing synthetic source gate is never promotion.
