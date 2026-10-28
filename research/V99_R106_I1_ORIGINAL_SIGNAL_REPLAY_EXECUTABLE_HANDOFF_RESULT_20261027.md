# V99 I1 — mandatory independent signal replay at executable original-source handoff (2026-10-27 23:54 BRT)

**SOURCE_ONLY/HOLD — NO PROMOTION. No economic TRAIN, no native ROI, no original options lifecycle.**

## Verified defect and fix
The prior executable `run()` accepted a `source_original: true` boolean and caller-provided SHA without independently re-executing original 182 OKX/DVOL signals; only the separate workflow enforced replay. This created a standalone provenance bypass if an original-looking options archive were later supplied. Preregistered before implementation in `V99_R106_I1_HANDOFF_ORIGINAL_SIGNAL_REPLAY_ENFORCEMENT_PREREG_20261027.md` (commit `7bea382`).

Fixed `research/tools/v99_r106_i1_fixed_train_handoff.py`: a nonfixture 661-day source now **requires** original OKX and Deribit DVOL receipt directories, independently loads them, and replays all 182 exact decisions with the independent causal oracle before reading option tape. Missing receipts -> `ORIGINAL_SIGNAL_REPLAY_RECEIPTS_REQUIRED`; a forged decision -> `ORIGINAL_SIGNAL_REPLAY_FAILED`. Synthetic fixtures remain blocked from promotion. Implementation `fd48436`, test `f032869`, real CI replay `67edae4`, syntax repair `16821e6`. An intermediate CI failed on a malformed function-signature newline and was corrected; do not cite the failed runs as success.

## Actual GitHub execution
[Actions 40623500068](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40623500068) **SUCCESS** at final commit `16821e6`. **11/11 tests passed**. Restored archived original TRAIN-only OKX spot (run `40019588739`), Deribit DVOL (run `40072202459`), and original 182-signal artifact (run `40326586848`). Original 182-signal independent oracle passed; a forged positive was rejected. Crucially, the **nonfixture executable handoff itself** independently replayed the 182 original decisions and rejected a forged input, then refused the missing full options tape as `INCOMPLETE_661_DAY_LIFECYCLE_ARCHIVE`. The production absence path separately reproduced `BLOCKED_ORIGINAL_LIFECYCLE_ARCHIVE_MISSING`.

**Counts:** 182 original signal rows; 180 fixed-tenor eligible BTC/ETH asset-weeks; 2 right-censored, not losses; **0/180** certified original complete option lifecycles. No new ROI, PnL, five-fold severe/supersevere economic TRAIN or validated candidate.

## Critical remaining blocker
No legally entitled, delivered and independently verifiable 2021-12-09..2023-09-30 Deribit BTC+ETH options full 661-day original bid/ask+size+dual-clock same-contract tape, nor dated account-specific historical fee tier, inverse-coin initial/maintenance/liquidation rules, delivery index/TWAP and settlement fees. A declared manifest or original spot/DVOL signal is not an executable fill. Verify Tardis **OPTIONS** invoiced 5-year grant and exact original fields/coverage or Amberdata equivalent before purchase. Once original bytes and terms are obtained, integrate source into original-native account and independently replay five TRAIN folds, 3x2 regimes, severe/supersevere, tails, drawdown and benchmarks. Freeze only on real gates; validation and final holdout stay sealed.

No orders; no Frozen, paper, legacy champion or dashboard performance promotion.
