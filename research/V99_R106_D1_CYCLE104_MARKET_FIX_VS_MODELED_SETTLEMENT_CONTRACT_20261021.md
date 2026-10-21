# V99 R106 D1 — C104 funding source contract v2 (2026-10-21 BRT)

**DATA_ONLY / HOLD — NO PROMOTION.** This is a source/accounting contract correction for the single existing D1 architecture, not a new alpha candidate, retune, or historical ROI.

## Proven semantic error

Legacy C102/C103 treat all scheduled public OKX 8-hour market funding fixes as if they were account-settled funding receipts, including flat-position hours. Public rate observations are not cash receipts. In the synthetic 120-hour negative control each cost scenario has **30 public market fixes but only 2 active-position modeled settlements**. C103 counts 30 account receipts. C104 v2 separates public `market_fixes` from `modeled_settlements`, forbids flat receipts and fake first-party account IDs, and binds modeled cash to signed native contracts, contract-era specifications, rates, marks, account cumulative cash, event count and settled keys.

## Actual local evidence

New local source-only verifier and adversarial test: `research/verification/independent_d1_funding_source_contract_cycle104.py` and `research/tests/test_v99_r106_d1_funding_source_contract_cycle104.py`. **17 new tests pass; full local D1 suite 890 passed + 120 subtests, zero failures.** Fixture funding cash `0.202` per scenario is synthetic, not historical return or authenticated receipt. The legacy C103 adapter intentionally rejects v2 journals until the downstream chain is migrated. No remote integrated CI or economic TRAIN was run for C104.

## Next mandatory gates

Version C102/C103 native journal adapters without inventing flat account receipts. Publish missing dependencies through authorized reviewed release (last inventory: 197 missing Python files). Run integrated GitHub CI, independently authenticate OKX historical funding, native fees and execution assumptions, then execute the frozen single D1 complete TRAIN (15,864 hours, 5 chronological folds, 3x2 regimes, severe/supersevere, independent accounting, benchmarks, drawdown and tail gates). Public exchange market fixes and hypothetical backtest cash must never be represented as actual account-settled receipts.

Validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 remain sealed. V16/V99 Frozen, legacy champion, paper/results and dashboard unchanged. **NO PROMOTION.**
