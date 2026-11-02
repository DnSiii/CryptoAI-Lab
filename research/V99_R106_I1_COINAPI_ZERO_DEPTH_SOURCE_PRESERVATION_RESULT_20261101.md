# V99 I1 CoinAPI zero-side source preservation — verified (2026-11-01 23:52 BRT)

**SOURCE HOLD / NO PROMOTION. No historical economics or orders.**

## Problem and fix
Previously, any zero bid/ask price or zero quote size in a possible original CoinAPI Deribit options Quotes gzip caused a whole-file rejection. That conflated **non-executable quote updates** with malformed source. This was a potential ingestion blocker, not evidence that any such row actually occurred in the unacquired historical archive.

Preregistered before implementation in `research/V99_R106_I1_COINAPI_ZERO_DEPTH_SOURCE_PRESERVATION_PREREG_20261101.md` (commit `e19667bf`). Source adapter commit `31f03a87` now accepts finite nonnegative original numeric fields and records `two_sided_positive_depth_rows` vs `non_executable_depth_rows`, never treats zero-sided updates as executable, and still vetoes negative/nonfinite/corrupt values, positive locked/crossed books, noncausal 100ns clocks, source key/date mismatch, changed gzip, and unlicensed intake. Adversarial controls in `39ad05cf`, newline fixture correction `f9a9dfbc`.

## Real GitHub verification
[GitHub Actions run 41380011874](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41380011874) on `f9a9dfbc`: **SUCCESS, 29/29 tests** (verified from job log), including all-zero quote, mixed non-executable/executable rows, negative/nonfinite and malformed numeric rejection, original-byte streaming, 100ns causal ordering, gzip corruption, original key and written-license guards. The CI source dependency step explicitly printed `BLOCKED: NO LICENSED 2021-2023 DERIBIT BTC/ETH COINAPI ARCHIVE; FORMAT TESTS ONLY; NO ECONOMICS/NO PROMOTION/NO ORDERS`.

## Precise blocker and next step
CoinAPI historical availability/entitlement for the fixed 2022-01-23 source day remains **unverified** because no lawful `COINAPI_API_KEY`/credits/rights document or actual vendor object was provided. An alternative is a lawful original Deribit options BBO/size/arrival/mark/expiry archive from another supplier, with independently verifiable chain and timestamp provenance. Even if licensed source bytes arrive, these adapter tests do **not** prove native lot-size conversion, dated fees, margin/liquidation/settlement, conservative simulated fills, 661-day coverage, five chronological severe/supersevere TRAIN folds, benchmark superiority, or independent economic gates. Existing 658/661 days missing and 0/180 economically certified lifecycles are **carried forward, not newly measured**. A signed source-only adapter cannot be promoted to an economic engine.

The prior C1, Donchian, cross-sectional candidates remain rejected. The sealed validation `[2023-10-01,2024-01-18)` and final holdout `>=2024-01-18` were not opened. Frozen V16/V99, paper, champion and dashboard results were not changed. No orders submitted.
