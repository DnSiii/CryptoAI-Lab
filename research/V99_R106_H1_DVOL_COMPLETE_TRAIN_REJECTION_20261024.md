# V99 H1 — original Deribit DVOL + OKX complete economic TRAIN: permanent rejection (2026-10-24 BRT)

**H1 PERMANENTLY REJECTED — NO RETUNE. DATA_ONLY/HOLD — NO PROMOTION.** A genuinely distinct options-implied forward-risk allocation failed the fixed economic gates. No new model is approved, no realized account/paper PnL is claimed.

## One-shot pre-registered evidence
- Original Deribit daily DVOL for BTC/ETH was collected across all five immutable TRAIN folds, 94/94 Monday decisions per asset with conservative strict t-1 daily-candle availability, independently verified 5/5: [Actions 40072202459](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40072202459).
- The **fixed H1 strategy and gates** were registered **before** reading any H1 economic results: [commit 72e301a](https://github.com/DnSiii/CryptoAI-Lab/commit/72e301a2f1ff6097188842c9f8bdc5aaa0cd47d9).
- [Actions 40072415531](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40072415531) **SUCCESS**: full 15,864-hour original first-party OKX spot TRAIN, 94 causal weekly option-implied-risk decisions, exact self-financing BTC/ETH/cash positions, four fee/slippage scenarios, passive benchmark envelopes, five chronological folds, six BTC regimes, daily/weekly/tail metrics and **independent original-DVOL-to-original-price-to-cash ledger/gate reexecution**. Independent adversarial cash/fee corruption check passed. Archived journal and oracle artifact **12551886316**.
- This green CI means the rejected economics are **accounted for correctly**, not that H1 is profitable or exchange-certified.

## Fixed TRAIN results (modeled, not actual account fills)

| Metric | Severe (0.12% modeled per side) | Supersevere (0.24% modeled per side) |
| --- | ---: | ---: |
| Total compounded ROI | **-27.9089%** | **-29.1556%** |
| Positive chronological folds | **1/5** | **1/5** |
| Fold 1 | -12.4446% | -12.6534% |
| Fold 2 | -26.2216% | -26.4589% |
| Fold 3 | -2.4279% | -2.6878% |
| Fold 4 | +15.9909% | +15.2330% |
| Fold 5 | -1.3426% | -1.6000% |
| Maximum drawdown | **-43.3076%** | **-43.6545%** |

**Seven of twelve named numerical/risk gates failed:** positive severe and supersevere ROI; severe >=4/5 folds; supersevere >=3/5 folds; both max drawdowns >=-35%; both daily profit factors >1; both positive after removing best day. H1 held cash at 16 of 94 weekly decisions (including the initial missing-previous-week decision). Stress scenarios and fixed benchmark envelopes were executed and independently reconciled; none of these rescues the failed economic gates.

## Consequence and exact blockers

**No validation or holdout access**. The validation interval [2023-10-01,2024-01-18) and final holdout >=2024-01-18 remain sealed. V16 Frozen, V99 Frozen, legacy champion, paper/results and order systems were not modified.

The Deribit DVOL source is first-party historical implied-volatility information, **not executable option quotes**. Original OKX historical opens are market prices, **not actual account fills**. The account's applicable 2021–2023 historical OKX fee-tier schedule and trade/execution statements are missing, so 0.12%/0.24% and shock costs are conservative **models**, not exchange-certified expenses. H1 uses spot only, so perpetual funding is **not applicable** to H1; any future perpetual strategy still requires settled funding and margin/lot specifications.

**Next justified path:** stop serial directional BTC/ETH allocation variants without an independent positive economic mechanism. If evaluating an options volatility-risk-premium strategy, first obtain auditable point-in-time executable bid/ask, margin/settlement/fee terms for options and verify an ex ante after-cost structural edge; DVOL alone cannot establish tradable profits. Alternatively source a different mechanism with full native execution evidence. Do not retune H1 or reopen rejected C1/C2/D1/E1/F1/G1. No fake deadline, no order placement, no promotion.
