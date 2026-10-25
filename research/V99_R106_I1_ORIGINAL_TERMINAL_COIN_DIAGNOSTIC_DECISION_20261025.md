# V99 I1 — Original quoted entry to original delivery-index terminal diagnostic (2026-10-25)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION. The observed partial sample is adverse under the fixed modeled cost scenarios, but it is not a tradable PnL or a full-TRAIN rejection.**

## Actual execution and independent replay

- Pre-result fixed protocol committed in `e56225f` (`research/V99_R106_I1_ORIGINAL_TERMINAL_COIN_DIAGNOSTIC_PREREG_20261025.md`), then original-source primary implementation `e8e09b7`, independent Decimal oracle `93dd4ca`, CI workflow `4ac0b92`.
- [GitHub Actions 40185981946](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40185981946) **SUCCESS**, actual archived original source artifacts downloaded. The job joined all 46 already verified original two-strike quoted put pairs to first-party original Deribit BTC/ETH TRAIN delivery prices on each option's exact expiry date. It rechecked source hashes, as-of/expiry partition and independent per-pair coin intrinsic, with no use of validation or holdout.
- Independent oracle **PASS 46/46** and three negative controls **REJECTED_SETTLEMENT**, **REJECTED_ROI**, **REJECTED_PROMOTION**. Output artifact `v99-i1-original-terminal-coin-diagnostic-40185981946`.
- Comparison `53c078ff...4ac0b921`: exactly four newly added research/workflow files, no Frozen, champion, paper/results, dashboard performance, order code or sealed partitions modified.

## Fixed source-conditional diagnostic (NOT investment returns)

| Fixed modeled entry cost path | Positive conditional terminal coin deltas | Nonpositive | Worst coin delta per assumed source unit |
| --- | ---: | ---: | ---: |
| Severe | **8/46** | **38/46** | **-0.1159881187** |
| Supersevere | **6/46** | **40/46** | **-0.1207881187** |

The sum of conditional modeled deltas across **untradeable, overlapping source units** is -1.2769494520 coin (severe) and -1.4977494520 coin (supersevere). **Neither number is PnL or portfolio return:** BTC and ETH coin units cannot be pooled as a single economic account without verified sizing/conversion; several adjacent spreads share underlying quotes; the two sampled Sundays are not a representative five-fold TRAIN; native displayed quote-size-to-contract units, account fees, liquidation and fill execution remain unverified. This calculation is a deliberately narrow source-to-terminal falsification, not evidence of realized profitability or loss. Do not tune or choose strategies from these outcomes.

## Actual remaining blockers

**Original market source:** full attributable 2021-12-09..2023-09-30 Deribit BTC+ETH option bid/ask/size and venue+arrival timestamps at all 91 maturity-eligible Mondays (182 asset-weeks) and throughout 21–45d holding/exit/settlement paths; current original entry samples only **4/182**, and certified complete executable lifecycles **0/182**. Non-sample historical Tardis access previously returned **HTTP 403** without a licensed entitlement. Alternative: independently documented equivalent vendor archive with 2021–2023 BTC+ETH point-in-time depth and gap manifest.

**Historical economic rules:** dated native quote-size/contract-unit interpretation, actual applicable account fee tier and expiry charges, coin collateral/margin/liquidation mechanics and conservative fill/exit model. The first-party original expiry-index source is already available; it is not the missing execution book.

**Next critical path:** acquire/verify one complete vendor sample covering entry and exit for both assets before purchase, then run the preregistered self-financing native coin portfolio accounting and independent five-fold TRAIN severe/supersevere, 3x2 regime, tail/DD, benchmark gates. Until then: no full economic TRAIN, no validation [2023-10-01,2024-01-18), no final holdout >=2024-01-18, no promotion, no paper/result mutation and no orders.
