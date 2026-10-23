# V99 R106 F1 — one-shot original-OKX basis convergence structural rejection (2026-10-23)

**DECISION: F1 CASH-AND-CARRY POSITIVE-BASIS CONVERGENCE MECHANISM REJECTED FOR THIS PREREGISTERED DESIGN; NO RETUNE. DATA_ONLY/HOLD — NO PROMOTION.**

## Actual execution and independent evidence

- Ex-ante fixed mechanism and two round-trip cost hurdles preregistered at commit [d21215d](https://github.com/DnSiii/CryptoAI-Lab/commit/d21215df971aae1afedf6915a7ecc46e3af623ee), **before** any F1 basis screen.
- Original first-party OKX four-leg 15,864-hour TRAIN archive from [Actions 40019588739](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40019588739), all original receipts independently reverified by the F1 workflow.
- [Actions 40041899186](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40041899186) completed successfully. An independent implementation re-read all four original hourly price streams, checked every hour, recomputed per-asset/per-fold daily counts, verified the precommitted 5-fold structural decision and exercised a corrupted-price negative control. The first workflow attempt 40041886014 failed due to a shell continuation syntax error; the workflow was fixed before the successful actual run, with **no changes to strategy, thresholds or partitions**.

## Numerical structural result — NOT PNL

- Original TRAIN: [2021-12-09, 2023-10-01) UTC, 15,864 hours, 660 UTC-midnight decision times with causal t-1 price information.
- Ex-ante all-in four-side modeled cost hurdles: **0.48% severe**, **0.96% supersevere**; these are not historical account fee receipts.
- Number of **distinct qualifying UTC decision days with any BTC/ETH positive perp premium strictly exceeding the respective hurdle**, folds 1 through 5:
  - Severe: **[0, 0, 0, 0, 0]**, **0/5 folds** with >=5 days.
  - Supersevere: **[0, 0, 0, 0, 0]**, **0/5 folds** with >=5 days.
- Preregistered necessary structural coverage was >=4/5 severe and >=3/5 supersevere; **both fail decisively**. No F1 economic backtest or PNL was computed; green CI means accurate falsification, not profitable trading.

## Consequence and remaining critical path

Do **not** build or retune this positive-basis convergence F1 design, relax thresholds, change the 00:00 UTC schedule after observing results, or claim there were no intra-day opportunities (they were not the preregistered decision times). D1 funding-only entry, E1 spot-beta, C1 and C2 are already rejected. Another serial candidate without an independently motivated economic mechanism would waste time and increase selection bias.

The real remaining deployment-grade external evidence gaps are: (a) applicable **historical account-specific OKX maker/taker fee-tier validity and instrument lot/margin rules**, (b) **historical exchange funding settlements** for 2021-12 to 2022-02 and principled reconciliation of off-grid published fixes if any future perp strategy needs funding, and (c) actual historical fills are **impossible** for unexecuted hypothetical orders, so any new strategy must use clearly labeled conservative executable fill/slippage and liquidation assumptions plus an independent accounting oracle. These missing documents do not excuse testing the already-available original market data; they do prohibit certified-real execution claims and premature promotion. Spot-only architectures can avoid funding, but E1's one-shot economic TRAIN already failed.

Frozen V16/V99, legacy champion, paper/results, public claims, sealed validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 were not touched. **No orders. No ROI. NO PROMOTION.** Next justified step: seek one independent mechanism with demonstrable after-cost economic basis and required source coverage *before* any new one-shot integrated engine. Do not claim a finished validated superior V99 until five-fold economic TRAIN, independent validation, and formal gates genuinely pass.
