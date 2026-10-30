# V99 R106 — Binance original funding 44-archive independent five-fold source result (2026-10-30 03:50 BRT)

**MATERIAL NEW ORIGINAL DATA, BUT SOURCE_HOLD / NO ECONOMICS / NO PROMOTION.** This is not a new alpha trial, not native account-settled funding, and not permission to reuse rejected D1 or to replace OKX receipts with Binance data.

## Fixed scope, provenance and real execution

- Original one-shot source contract preregistered at [a3af22f](https://github.com/DnSiii/CryptoAI-Lab/commit/a3af22f035271f2df0b74f261959451d60a9376e) **before** implementation or original network requests. Exactly [2021-12-09, 2023-10-01) UTC, BTCUSDT and ETHUSDT Binance USD-M perpetual funding, 22 monthly archives per asset (2021-12 through 2023-09). Official original archive `data.binance.vision/data/futures/um/monthly/fundingRate/`, plus each publisher `.CHECKSUM`. Source-only, no validation/holdout.
- [Actions 41016094695](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41016094695) **SUCCESS** and [Actions 41016164149](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41016164149) **SUCCESS**: **44/44 original ZIPs** independently matched their Binance-published SHA256 and original CSV structure. **1,983 in-TRAIN original rate rows per asset** (2,007 including pre-TRAIN December), strictly increasing, no duplicate in-TRAIN timestamps, all `funding_interval_hours=8`. Separate independent original-byte ZIP/CHECKSUM oracle recomputed five folds and flags. Source metadata artifact 12959182881, raw publisher ZIPs and checksums removed before upload.
- First result showed **821/1,983** original `calc_time` events exactly on nominal 8h UTC grid per asset, **1,162/1,983** off-grid. The follow-up timestamp diagnostic was separately fixed before re-reading original bytes at [b677929](https://github.com/DnSiii/CryptoAI-Lab/commit/b6779298805f51dc2b1bd9e5903831117fc0ad7a). Final [Actions 41016303777](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41016303777) **SUCCESS**: independently verified all original timestamp residuals, with exactly the **same distribution for BTC and ETH**. Off-grid events are **+1 to +31 milliseconds after** nominal 8h UTC boundaries, never negative or farther than 31 ms. This is strong evidence of an archive `calc_time` timing convention, **not** independent proof of actual private funding cash settlement or permission to backdate an observation. An intermediate [Actions 41016297983](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41016297983) failed because primary diagnostics had been committed before the separate oracle was updated; the complete final oracle run passed without changing original data, fold boundaries or the exact-clock gate.

| Original chronological fold | Expected 8h slots | BTC exact native calc_time | ETH exact native calc_time |
| --- | ---: | ---: | ---: |
| 1 | 397 | 127 | 127 |
| 2 | 397 | 129 | 129 |
| 3 | 396 | 133 | 133 |
| 4 | 397 | 99 | 99 |
| 5 | 396 | 333 | 333 |
| **TOTAL** | **1,983** | **821** | **821** |

The 1,162 off-grid rows per asset are **not missing archived rates**. Every original month has archived rates, including **December 2021**, which was absent in the separate OKX source route. This finding is **Binance-specific** and does not repair the OKX missing December, native account fee tier, margin, actual funding cash, fills, or any previously rejected strategy.

## Decision and next real step

**SOURCE_HOLD (strict original exact-clock contract), NO PROMOTION.** The original 44-archive coverage and 0–31 ms offset result justify one *targeted* independently preregistered corroboration against Binance's own historical `/fapi/v1/fundingRate` `fundingTime` timestamps and a dated official explanation of `calc_time` semantics. Do **not** silently snap or alter the existing 821/1,983 strict source result. If first-party evidence establishes nominal settlement clock vs later archive calculation timestamp, a **new, separate source-only causal timestamp-binding rule** may be preregistered; the actual arrival time must remain causal. The independent economic/accounting gate remains closed until a genuinely distinct, rational full-system hypothesis, native price/fee/funding/margin/execution provenance, severe/supersevere modeled economics, five TRAIN folds and risk gates are all established. This is **not** an invitation to rerun rejected D1 on Binance.

**I1 unchanged:** 658/661 licensed Deribit BTC+ETH historical quote days absent, 0/180 option lifecycles economically certified; missing written license, full original BBO/size/clock archive, original marks/settlement, native dated fee/margin/delivery terms and conservative fill evidence. The Binance funding discovery is a *different venue/source*, not a substitute for options data.

No economic TRAIN or ROI, no real orders, no private account funding receipts, no validation [2023-10-01,2024-01-18), final holdout >=2024-01-18, Frozen V16/V99, paper/results, legacy champion or public performance claim touched. **NO PROMOTION.**
