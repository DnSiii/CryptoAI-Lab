# V99 R106 D1 — C100 trade-to-native-fill identity (2026-10-20)

**DATA_ONLY/HOLD — NO PROMOTION.** New versioned, TRAIN-only verifier; no strategy parameter changes, no economic ROI, no validation/holdout, no orders or paper publication. C1/C2 remain permanently rejected.

## Scientific gap
C92 independently computes claimed closed-pair trade PnL and C93 verifies a separate hourly native ledger, but the C98/C99 chain does not prove that the claimed closed-pair entries/exits are the same events as the native hourly executions. Equal aggregate net PnL and final NAV cannot establish fill identity. In a synthetic negative control, shifting a C92 trade opening by one hour retained valid C92 accounting but no longer matched the native entry event.

## Preregistered C100 verifier
New `research/verification/independent_d1_trade_fill_identity_cycle100.py` is additive and fail-closed. Before invoking C99/C98, it requires both scenario journals, strictly UTC TRAIN-only hourly frames, and exact event-multiset parity of each C92 closed-lot opening/closing against C83 native perp fill **asset, hour, side, fill price, base quantity**, plus native spot fill **asset, hour, side, fill price**. Supports split closed lots via quantity aggregation and rejects extra/missing native fills. Floats/nonfinite claimed fill quantities and prices fail closed. C100 never changes trading decisions, benchmarks, risk parameters, or C97 numerical gates.

## Explicit limits
The oracle binds modeled *perp* size and spot price/side but does **not** independently reconcile spot gross base-size when native fees are paid in base, nor match every C92 trade-level funding fix to its native settlement receipt. Those gaps remain mandatory before economic authorization. C82/C83/C93/C94/C92/C97/C99 are still required; first-party OKX history, fee tiers, settled funding, original execution fills, independent economic replay and five-fold severe/supersevere gates remain unavailable. No output of this verifier authenticates exchange data.

## Local synthetic evidence
- 13/13 C100 adversarial tests passed, including C92-accepted time-shift counterexample, ghost trades, fill price/size/side mismatch, extra fills, spot-price mismatch, nonfinite receipt, sealed-window rejection and downstream short-circuit.
- Entire local D1 suite excluding the resource-heavy full-calendar synthetic file: **825 tests + 120 subtests passed**; no failures.
- The full-calendar synthetic test remains **not claimed passed** this cycle.
- Latest remotely observed branch HEAD at inspection: `04caa20ca0be14465b9f35fd58e58c653867aa9d`. Latest observed branch CI was synthetic calendar Action 39128800765 on 2026-10-18, not a D1 economic backtest.

## Next justified step
Publish C100 source/tests only by an authorized route and run integrated remote CI; complete funding-fix-to-native-receipt and spot-fee-base quantity binding before using C100 as an economic gate. Collect original OKX TRAIN-only data for 2021-12-09 through 2023-10-01; independently replay 15,864 hours with five chronological folds, six regimes, severe/supersevere, drawdown, tail, and all four preregistered benchmarks. Reject any failed gate. Validation from 2023-10-01 and final holdout from 2024-01-18 remain sealed. **NO PROMOTION.**
