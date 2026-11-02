# V99 I1 CoinAPI original Quotes dialect + 100ns compatibility — verified result (2026-11-01 22:54 BRT)

**Decision: SOURCE HOLD / NO PROMOTION.** This is a deterministic ingestion correctness fix, not a historical economic result.

## Actual vendor discrepancy
- Official [Quotes dataset guide](https://www.coinapi.io/products/flat-files/docs/datasets/quotes) prints comma-separated seven-field CSV.
- Official [Quotes Samples](https://www.coinapi.io/products/flat-files/docs/data-samples/quotes) prints semicolon-separated seven-field CSV for spot, futures and options examples, with seven fractional timestamp digits; e.g. arrival `2025-09-01T00:00:00.2351738`.
- [Flat Files standards](https://www.coinapi.io/products/flat-files/docs) specify `fffffff` (100ns) UTC output. The prior adapter accepted comma only and rejected nonzero seventh fractional digit. It could reject actual vendor-original data before any economics.

## Preregistration, implementation, verification
- Before code: `research/V99_R106_I1_COINAPI_DIALECT_100NS_PREREG_20261101.md`, commit `4b1a6313`.
- Implementation: `8f77b296` (both exact vendor header dialects, single dialect locked for whole file, exact 100ns event/arrival ordering and first/last 100ns metadata); `79901de` adds adversarial synthetic tests; `cfcf55d` fixes streaming dialect metadata propagation exposed by actual CI.
- **Real remote [GitHub Actions 41374802348](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41374802348): SUCCESS, 26/26 tests.** Earlier runs `41374753493` and `41374766031` failed during development; errors corrected before final successful run. The tests include comma and semicolon examples, nonzero seventh-digit 100ns, within-microsecond causal reversal, within-microsecond arrival ordering, mixed dialect rejection, sub-100ns rejection, gzip truncation, source key and license guards.
- The microsecond fields in output are explicitly **floored display-only**; exact causal ordering uses integer 100ns ticks. No ROI or fills inferred.

## Unresolved critical path
No licensed CoinAPI 2021–2023 BTC/ETH Deribit options original archive was obtained or processed in this run. The fixed 2022-01-23 CoinAPI S3 listing is still externally blocked without a lawful Flat Files `COINAPI_API_KEY` and credits/license. Existing reported **658/661 original days absent** and **0/180 certified option lifecycles** remain unchanged (not remeasured here). A credential alone is not enough: need complete entry/mark/exit original BBO/size and receipt clocks, source-unit conversion, dated native fee/margin/liquidation/settlement terms, independently replayed conservative simulated execution, full five-fold severe/supersevere TRAIN and gates.

No historical economic TRAIN, no validation/holdout opening, no freeze, no promotion, no orders. V16 Frozen, V99 Frozen, paper, champion and all sealed windows untouched.
