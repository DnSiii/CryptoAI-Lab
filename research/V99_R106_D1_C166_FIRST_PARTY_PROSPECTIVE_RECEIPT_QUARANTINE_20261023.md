# V99 R106 D1 C166 — verified prospective receipt quarantine and native minimums (2026-10-23 BRT)

**Decision: DATA_ONLY/HOLD — NO PROMOTION.** No authenticated historical economic TRAIN, no validated ROI, no validation or final holdout access, no orders and no changes to Frozen, paper or legacy champion.

## Exact additive implementation and independent source evidence

- Branch `research/v99-r106-native-all-regime-engine`. Added `research/verification/independent_d1_c166_prospective_receipt_quarantine.py`, `research/tests/test_v99_r106_d1_c166_prospective_receipt_quarantine.py`, and `.github/workflows/v99-r106-d1-c166-receipt-quarantine.yml`. No original strategy/engine parameter was modified.
- Inspected the independently maintained, append-only `research/v99-r106-live-receipts` branch, **hour 2026-10-23T18 UTC**. Source collection was actually run: market Actions **40005383339**, terms/funding-notice Actions **40005546266**. These are contemporaneous first-party HTTP observations, NOT signed historical account statements.
- New C166 CI independently fetched that separate receipt branch read-only and recomputed **six raw SHA-256 hashes** for BTC/ETH perpetual market, native contract metadata and funding notices. It did not copy receipts into the research engine or treat them as historical.
- The contemporaneously observed OKX linear USDT-swap contract geometry implies minimum order base units **BTC 0.0001** and **ETH 0.001**, computed from `ctVal`, `lotSz`, and `minSz` (all observed in October 2026). These are **NOT 2021–2023 specifications**, do not prove historical spot lot sizes and do not certify the modeled C139 fills.
- Public funding notices are **not actual settled funding cashflows**; public metadata is **not an account-specific historical fee schedule**; current swap candles do not supply the required 2021–2023 BTC/ETH spot+perpetual four-leg market history. No authenticated execution/fill/slippage journal was found.

## Actually executed remote CI

- Initial C166 workflow: **40007115039**, success, 68 pytest + 87 unittest = **155/155** tests.
- An intermediate commit **dd7b0e0** introduced mandatory native `minSz` verification before its synthetic test fixtures were updated; CI **40007216078** failed as expected on `C166_BAD_CONTRACT_QUANTITY`. This was a temporary source/test synchronization failure, not a market result.
- Corrected both code and fixtures and added minimum-order negative controls. Final run **40007231330**, job **120598118189**, commit **cda431640bcd62335199c33cf6be85a7ff2772c3**: **completed/success**. Logs confirm **70/70 pytest + 87/87 unittest = 157/157**; six real receipt hashes verified; source permission assertion passed. No historical economics were executed.
- The output explicitly reported `train_market_economics_authorized=false`, `exchange_account_history_authenticated=false`, `validation_opened=false`, `final_holdout_opened=false`, `promotion_authorized=false`, and `orders_enabled=false`.

## Scientific disposition and next critical path

C166 closes a concrete contamination risk: fresh, correctly hashed 2026 receipts **cannot** be silently backdated to preregistered TRAIN [2021-12-09,2023-10-01), nor can observed funding forecasts be mislabeled as realized settlement or native public contract metadata as an account fee tier. This is source/provenance hardening, **not** proof of strategy alpha.

Next, prioritize completing the original C141–C147/C152 integrated D1 source chain without inventing unavailable local artifacts, then binding **historical first-party four-leg paired hourly prices**, dated contract/spot lot terms, historical account-native fee tiers, settled funding cashflows and execution/slippage receipts. Only after a genuine source gate can the **single** preregistered D1 complete TRAIN economic trial run with 15,864 hours, 5 chronological folds, 3x2 regimes, both severe/supersevere cost paths, independent NAV/ledger replay, drawdown, tails and benchmark envelope. Reject failed gates; freeze only a qualified TRAIN winner before opening sealed validation. The final holdout remains locked.

**No historical economic trial dispatched. No paper publication, order, model promotion or immutable-path edit.**
