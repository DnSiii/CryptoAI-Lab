# V99 I1 — same-expiry single-settlement fail-closed rule (preregistered 2026-10-26 08:xx BRT)

**Before implementation; SOURCE_ONLY/HOLD, NO PROMOTION.** The native-coin replay currently permits `settle(wallet, one_name, expiry, ...)` even when another spread has the **same expiry** and no later-expiring survivor. This is a partial release of a cohort that should settle at one original delivery index and one atomic cash/margin transition. It can expose a fictitious intermediate available-collateral state and an order-dependent settlement result. The existing `settle_batch` is the already-implemented full-cohort route.

Fixed corrective acceptance, without parameter search or strategy tuning:

1. `settle` must reject any same-expiry sibling **regardless of later expiries**, with `SAME_EXPIRY_ATOMIC_BATCH_REQUIRED`. A unique due position with later-expiry survivors retains the pre-existing synchronized mark/index and maintenance checks.
2. Independent Decimal oracle must separately reject a single `settle` event while another due sibling remains, with `REFERENCE_SAME_EXPIRY_ATOMIC_BATCH_REQUIRED`.
3. Migrate the existing two-position same-expiry synthetic journal to one `settle_batch` event, preserving exact final cash, reserved collateral, positions and settled IDs; reexecute both severe and supersevere and verify against independent oracle.
4. Keep an independent positive single-due/mixed-expiry journal and adversarial negatives (including a same-expiry-only wallet, without a later survivor). No use of future validation/holdout, no new alpha, no orders, no invented ROI.

Success is **only accounting integrity**, never a complete engine, native historical terms, executable options data, economic TRAIN or promotion. No changes to V16 Frozen, V99 Frozen, paper-results, champion, or public dashboard. Original licensed BTC/ETH 2021–2023 full lifecycle BBO+size+clocks, fees, margin and delivery receipts remain required; currently 0/182 complete certified lifecycles.