# V99 I1 — ex-ante source-driven CASH veto provenance gate (2026-10-29 05:xx BRT)

**DATA_ONLY/HOLD — NO PROMOTION.** This preregistration is before implementation and before any new economic run. It does not authorize model selection, fee assumptions, validation, holdout, or orders.

## Fixed falsifiable rule

For each of the immutable 180 Monday BTC/ETH TRAIN intents and for EACH severe/supersevere decision path, bind the independently original-byte-verified full 28–35d predecision option book to the matching causal signal and OPEN/CASH decision. A positive-signal OPEN is impossible if the full original eligible-tenor book is empty: fail before NAV. A positive-signal CASH labeled `RISK_VETO` when the eligible-tenor book is empty is an unsubstantiated risk attribution: fail before NAV; the only source-compatible reason in this case is `NO_ELIGIBLE_FIXED_VERTICAL`. If positive-signal CASH is labeled `NO_ELIGIBLE_FIXED_VERTICAL` and the observed tenor book is empty, record **observed empty book conditional on archive completeness**, never certified absence of market liquidity. If the tenor book is nonempty, neither `NO_ELIGIBLE_FIXED_VERTICAL` nor `RISK_VETO` is independently proven without authenticated underlying index, lot conversion, margin and fees; count both as unverified. Negative original signals remain CASH. Never infer an executable spread from the mere presence of quotes.

## Implementation/verification acceptance

- Must reject mismatched 180-row intent/book/decision grids, malformed source books, contradictory empty-book OPEN and mislabeled empty-book risk veto, and any caller-provided certification flag.
- Independently recompute all per-scenario classifications from the original-derived full books without importing the primary classifier; verify all counts and prohibit a forged source-certification claim.
- Integrate this gate into the existing original-to-provisional runner **after** independent original quote-book verification and **before** NAV. No synthetic fallback when licensed source absent.
- Exercise adverse controls in CI on synthetic original-shaped data; actual licensed original historical data are still missing, so no economic trial or numeric gate can pass because of these tests.
- No change to I1 strategy thresholds, tenor, fold boundaries, price/fee assumptions, Frozen, paper/results, champion, validation [2023-10-01,2024-01-18), final holdout >=2024-01-18, or orders.

**Exact external blocker:** licensed 661-day original Deribit BTC/ETH options BBO+size+dual clocks (2021-12-09..2023-09-30), native dated lot/fee/margin/settlement evidence, and independent capture completeness. No fee/fill proof can be fabricated from original BBO alone.