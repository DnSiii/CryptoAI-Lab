# I1 cross-expiry settlement safety — verified result (2026-10-26 06:45 BRT)

**SOURCE_ONLY/HOLD — NO PROMOTION.** The previous native coin wallet could settle an earlier-expiring spread while carrying a later-expiring short spread at an old mark, and advance account time without proving surviving maintenance NAV. This is a real accounting safety defect, not a newly discovered trading edge.

## Implemented
- Ex-ante preregistration `V99_R106_I1_CROSS_EXPIRY_SETTLEMENT_SAFETY_PREREG_20261026.md`, commit `4d10c16`.
- Production `settle` now requires each later-expiring survivor to have a fresh mark at the exact earlier expiry settlement timestamp, using the identical original underlying delivery index. It refuses partial mixed same-expiry/later-expiry settlements absent an atomic batch; it independently rechecks post-settlement maintenance NAV, refusing to carry forward an insolvent account. Commit `44d7cbc`.
- Independent Decimal oracle rejects the same stale/missing/index-mismatched surviving marks and post-settlement maintenance breach without importing the production function. Commit `6d38311`.
- Adversarial two-expiry production and independent oracle tests added, commit `4e10967`. GitHub Actions [40301996771](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40301996771) **SUCCESS**, **20/20 synthetic unit tests**. The independent 8-event journal also reconciled both severe and supersevere **synthetic** scenarios; those runs do not establish historical returns.

## Unchanged critical economic blocker
**0/182 certified complete original BTC/ETH historical option lifecycles**. No authorized original full 2021-12..2023-09 quote/size/arrival and complete holding-period mark/exit/settlement archive, original native lot/fee/margin/liquidation terms and independently verified executable size-aware fills are present. Historical TRAIN, five-fold robustness, 3x2 regimes, severe/supersevere economic outcomes, independent economic replay, validation and final holdout therefore remain **NOT RUN**. Tardis/CoinAPI entitlement with vendor-confirmed full coverage or equivalent authenticated archive is the source alternative; the existing partial original captures cannot be extrapolated to missing lifecycles.

**Limitations:** this safety patch is still model-only. Same-expiry batch plus later-expiry positions require a separate atomic settlement implementation before accepting that portfolio path. No orders, no proven ROI, no frozen/paper/champion/holdout mutation. Green CI is NOT an economic gate.
