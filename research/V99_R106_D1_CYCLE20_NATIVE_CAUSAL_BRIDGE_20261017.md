# V99 R106 D1 — cycle 20 native causal bridge (2026-10-17)

**DATA_ONLY/HOLD — NO PROMOTION.** This is a research checkpoint, not a published trading model, a historical backtest, or proof of OKX fills/funding.

## Critical integration gap found
The preregistered causal controller recomputed t-1 intent but called `D1StrictEventClock.rebalance(decision)` without native contract specifications. In `require_native_settlement=True`, every nonzero position failed with `NATIVE_CONTRACT_SPECS_REQUIRED_FOR_ENTRY`. The prior 172 passing synthetic tests and independent native ledger oracle did not exercise this combined entry path.

## Local repair and reproducible checks
A **local, not yet merged** patch adds keyword-only `contract_specs` to the causal controller, checks both BTC/ETH identities and validity windows, rejects native specs in nonnative mode, and forwards the specs to the native lot-quantized ledger. It does not change any preregistered alpha rules, fees, scenario assumptions or time partitions.

**179/179 local D1 tests pass** (+7 new), including native causal entry, missing/stale specs, coarse-lot cash outcome, native two-asset mark-price settlement after causal entry, and second-asset mismatch atomic rollback. A separate independent synthetic oracle re-ran 2×2,000 hours with 498 modeled funding events and 84 lot-quantized rebalances per scenario; maximum Decimal NAV residual 6.8e-15. The new controller-to-native integration is exercised by the new tests, not by that independent oracle.

## Scientific embargo
No first-party historical OKX fill receipts, actual settled account funding, fee tier or native historical settlement marks have been authenticated. No historical TRAIN economics or ROI was calculated. The sealed validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 remain unopened. C1 and C2 remain rejected; frozen baselines, paper and legacy champion remain untouched.

**Next:** integrate the 41-file local patch into the research branch, execute D1 CI, collect authentic historical source evidence, then run strictly TRAIN-only economics. A passing synthetic test or Action cannot authorize promotion.