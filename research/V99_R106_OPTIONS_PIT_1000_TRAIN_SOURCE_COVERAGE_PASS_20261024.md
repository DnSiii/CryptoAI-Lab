# V99 — fixed 1000-depth weekly PIT options source remedy result (2026-10-24 BRT)

**DATA_ONLY/HOLD — NO PROMOTION.** A source-coverage gate passed; **no economic engine, historical ROI, account PnL, executable option quotes, real fills or native fee certification exists**.

## Direct evidence and independent oracle

- Pre-fixed depth-only remedy: [source preregistration](V99_R106_OPTIONS_PIT_1000_SOURCE_REMEDY_PREREG_20261024.md). It preserved all decision clocks, TRAIN folds, 24h lookback, strict t-1, 6h maximum age, expiry bands, 2-strike/side/band rule and 70%/4-fold coverage gate. Only the source request depth changed from 100 to 1000 to address **188/188 truncated 100-trade samples**.
- [GitHub Actions 40067965880](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40067965880) **SUCCESS**: original historical Deribit option trade receipts and an independently implemented reexecution of SHA-256, timestamp, expiry/strike, fold and coverage decisions.
- **94 fixed weekly decisions x 2 currencies = 188/188 first-party successful responses**, no source errors; **188,000 sampled option trade rows**; all 188 responses have `has_more=true`, so these still do **not** prove complete 24h market coverage. Original source and summary: Actions artifact **12549928073**.
- Preregistered eligibility passed **186/188 currency-decisions**; the two failures were sparse long-dated put strike observations. All short-call, short-put and long-call sample groups met their two-strike lower bound.

| TRAIN fold | BTC covered | ETH covered | Fold passes >=70% both? |
| --- | ---: | ---: | --- |
| 1 | 19/19 | 19/19 | Yes |
| 2 | 19/19 | 19/19 | Yes |
| 3 | 18/19 | 19/19 | Yes |
| 4 | 18/18 | 18/18 | Yes |
| 5 | 19/19 | 18/19 | Yes |
| **Total** | **93/94** | **93/94** | **5/5 folds** |

**Decision:** `PIT_SAMPLE_SUFFICIENT_FOR_NEXT_DESIGN` — this is permission to design and preregister **one** distinct integrated economic engine; it is **not** an economic pass or model promotion. The 100-trade contract remains failed as originally tested. The 1000-trade remedy shows that its failure was primarily sampling truncation, not a demonstrated lack of source trades.

## Critical remaining path

Before any TRAIN PnL, independently derive stable **causal, comparable** options IV/skew/term-structure information from original trade-level IV and **contemporaneous** underlying index/strike/expiry, with explicit handling of trade-age, moneyness, duplicates and expiry mixing. Trades do not provide executable bid/ask quotes. Preregister one economically rational full portfolio engine with original OKX spot/perp cashflows and exact five folds/six regimes, severe/supersevere fees and shocks, tail/DD and fixed benchmarks. Native historical OKX account fee tier, settled funding and execution evidence remain unproven; modeled costs must be labeled modeled. Independent original-price-to-cash replay is mandatory. Only a successful frozen TRAIN may open sealed validation [2023-10-01,2024-01-18); final holdout >=2024-01-18 remains sealed.

**NO PNL. NO ORDERS. NO PAPER WRITES. NO PROMOTION. V16/V99 Frozen, legacy champion and holdout untouched.**
