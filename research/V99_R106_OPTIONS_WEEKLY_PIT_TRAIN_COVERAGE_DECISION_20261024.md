# V99 — weekly PIT options information source decision (2026-10-24 BRT)

**DATA_ONLY/HOLD — NO PROMOTION.** This is a *source information coverage* decision, not a new trading strategy, PnL backtest, historical alpha result or exchange-certified executable quote test.

## Real CI and independent reexecution

- [GitHub Actions 40067800594](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40067800594): **SUCCESS**, including the independent oracle for original raw-byte SHA-256, strict t-1 timestamps, option instrument/expiry/strike parsing, 5 chronological folds, weekly eligibility and final coverage decision. Original receipts and full summary archived as artifact **12549358904**.
- Exactly **94 fixed Monday 00:00 UTC decision dates**, two assets (BTC and ETH), **188/188 successful first-party historical Deribit API responses**, no source errors. Exactly 100 trade rows per response (**18,800 sampled option trades**); **188/188 have `has_more=true`**.
- These are the **latest 100 trades from each 24-hour lookback**, not the full option market. All sampled source rows are strictly earlier than the decision. No validation or final holdout was queried.

## Preregistered lower-bound coverage gate (not an alpha test)

Fixed before retrieval in [preregistration](V99_R106_OPTIONS_WEEKLY_PIT_COVERAGE_PREREG_20261024.md): at each weekly decision, BTC and ETH each require >=2 distinct strikes of calls and puts in both 7–45d and 46–120d expiry bands, with option trade IV not older than six hours. A fold requires >=70% of decisions covered **for both assets**, with >=4/5 folds required for proceeding to engine design.

| Chronological TRAIN fold | BTC eligible Mondays | ETH eligible Mondays | Fold passes both >=70%? |
| --- | ---: | ---: | --- |
| 1 | 6/19 | 10/19 | No |
| 2 | 1/19 | 7/19 | No |
| 3 | 3/19 | 5/19 | No |
| 4 | 10/18 | 3/18 | No |
| 5 | 3/19 | 1/19 | No |
| **Total** | **23/94** | **26/94** | **0/5 folds** |

Across the 188 samples, fewer than two distinct strikes appeared in **88 long-dated call** samples and **91 long-dated put** samples (vs only 6 short calls and 13 short puts). This is evidence that the bounded 100-latest-trades **sampling contract** is especially weak for the long maturity band. It is **not** evidence that the exchange had no such instruments/trades: all 188 samples were truncated (`has_more=true`).

## Decision and actual blocker

**The preregistered weekly 100-most-recent-trades information contract fails 0/5 TRAIN coverage folds. Do not use it as a causal full-chain options signal or score a strategy on it.** Do not change coverage thresholds after seeing these numbers to manufacture a pass. This result **does not reject the entire options information family**: a separate fixed source design with complete chronological pagination or first-party historical option-chain snapshots could establish whether an actually observable two-maturity IV/skew state exists. Do not treat trade IV as executable option bid/ask.

Before a legitimate complete new motor: obtain sufficiently broad original PIT options coverage (or switch to a separately justified economic mechanism), fixed causal architecture, original native OKX fees/terms/funding where relevant and conservative spot/perp execution evidence; then independent severe/supersevere full TRAIN accounting, five folds, six regimes, risk/tail/DD and benchmarks. No new candidate is eligible for sealed validation until TRAIN passes and is formally frozen.

**No economic TRAIN. No ROI. No model promotion. No orders. No paper writes. Frozen and sealed validation/holdout preserved.**
