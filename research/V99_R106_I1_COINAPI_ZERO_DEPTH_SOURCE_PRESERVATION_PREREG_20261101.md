# V99 I1 — preregister zero-side original quote preservation (2026-11-01 23:xx BRT)

## Defect hypothesis and fixed scope
The CoinAPI source-only adapter currently calls `positive` on all four top-of-book price/size fields, aborting the **entire** licensed original daily gzip if any row has a zero price or zero size. A zero side is not executable depth and must never be used to infer fills; however a source capture containing a non-executable quote update should not be mistaken for a malformed/unusable original file. This is a robustness fix to unblock processing of possible sparse historical option books, **not** a claim that any such historical row has been observed or that CoinAPI guarantees zero-side semantics.

## Ex ante implementation and tests
- Keep strict original gzip SHA256/rehash, key/date/symbol binding, exact two-clock 100ns causality, monotonic arrivals, exact CSV dialect and license guard.
- Accept finite **nonnegative** prices and sizes at the raw *source-format* layer. Reject negative, NaN, infinity, invalid numbers, and crossed/locked books when both sides have positive price.
- Count a row as **non-executable** if either bid/ask price or either size is zero; never count it as two-sided positive-depth liquidity. Preserve both counts in the report, including a zero-executable-row file.
- Adversarial tests: zero bid/ask, zero bid/ask size, all-zero rows, mixed zero/valid rows, negative/nonfinite veto, crossed positive book veto, existing license and clock tests.
- Source-only: do not convert vendor sizes to native lots, do not construct fills, do not run sealed validation/holdout, do not claim profitability. No changes to Frozen, paper, champion or any trading order path.

## Promotion gates
Only a lawful original 2021-12-09..2023-09-30 Deribit BTC/ETH options quote/size/arrival/mark/expiry archive, independent first-party venue listing/terms, conservative size-aware execution, five chronological TRAIN folds, severe/supersevere and independent accounting can advance economic certification. The CoinAPI key/credits/rights and source data are external dependencies. Until then **SOURCE HOLD / NO PROMOTION**.
