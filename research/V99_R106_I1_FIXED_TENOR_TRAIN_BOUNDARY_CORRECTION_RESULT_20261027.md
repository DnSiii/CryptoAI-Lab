# V99 I1 — fixed-tenor TRAIN boundary correction: actual CI and independent original-source veto (2026-10-27 08:49 BRT)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION.** This correction does **not** constitute an economic backtest, validated trading strategy, positive ROI, exchange fill, historical native margin certification, or authorization to open validation/holdout.

## Material discrepancy corrected, without strategy retuning

The original causal signal schedule uses 91 Mondays per asset based on a 21-day minimum, giving 182 BTC+ETH decisions. The separately preregistered fixed put vertical requires a 28–35-day maturity and a contractual expiry **strictly before 2023-10-01 UTC**. The 2023-09-04 Monday is only 27 days before the sealed boundary; a 28-day vertical is impossible even with a perfect option archive. This yields **90 structurally eligible Mondays per asset (180 potential asset-weeks)**, plus **2 structurally censored cash decisions** on 2023-09-04. The original 182 source signals remain valid observations, not 182 executable entry opportunities. The 2023-08-28 decision remains potentially eligible; the rule and portfolio logic are unchanged.

Preregistered first at commit `e976e60fba435cd873cce655f8da3841bad35b46`. The primary bridge now labels the impossible decision `CASH_FIXED_TENOR_RIGHT_CENSORED`, preserving the causal cash clock and rejecting invalid quotes before classification. A separately implemented oracle independently recomputes the inequality, rejects forged censored cash on 2023-08-28 and generic cash on 2023-09-04, and validates severe/supersevere wallet invariants. No tuning, no new alpha candidate, no PnL or opened sealed period.

## Actually executed on GitHub

- [Actions 40498977600](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40498977600) **SUCCESS**, final head `49849ab4a601400c6c36f6e51f711209cb09608a`. **22/22 deterministic synthetic integrity tests** passed, including both scenario cost paths and the new boundary falsification.
- Crucially, this same CI restored original archived OKX/Deribit TRAIN source receipts and independently replayed the original signal/options byte join. Result **182 original signal observations, 132 positive ex-ante signals, 0 synchronized original source-ready asset-weeks, 0 certified complete option lifecycles**. Independent source oracle confirmed the veto and rejected forged intersections and source hashes. These are *not* profitable folds or options trades.
- [Compare baseline..head](https://github.com/DnSiii/CryptoAI-Lab/compare/2bea121416d151ed821068abdfa2119416d43495...49849ab4a601400c6c36f6e51f711209cb09608a): four commits, exactly four research-only paths (preregistration, primary bridge, independent oracle, tests); no Frozen, paper/results, legacy champion, dashboard, validation or holdout changes.

## Unchanged genuine critical blocker

No lawful, authenticated, complete **2021-12-09..2023-09-30 BTC+ETH Deribit OPTIONS** original bid/ask+displayed sizes with exchange/local arrival clocks and complete 21–45d lifecycle/expiry coverage; no dated account-specific native fee/delivery/margin/liquidation documentation or independently bound historical execution source. The GitHub Tardis credential was absent in the most recent actual authenticated probe, so historical economic TRAIN remains blocked. The nonfixture execution adapter deliberately fails closed until independent receipt attestation exists; caller booleans cannot unlock it. A verified alternate vendor with the same field, coverage, license and cost evidence is acceptable. **Next: source acquisition and independent byte-bound attestation, then a single fixed I1 five-fold economic TRAIN with severe/supersevere, 3x2 regimes, tails, DD and benchmark envelope; no model promotion before all gates.**

No orders, ROI, frozen modifications, paper updates, validation or final holdout access.
