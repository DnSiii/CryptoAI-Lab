# V99 I1 — original last-receipt revocation preregistration (2026-10-27, TRAIN only)

**Scope and decision fixed before implementation.** The 661-day I1 source-only scanner currently marks an exact contract/day as present if *any* valid row appeared, and remembers the last *valid* Sunday entry quote. A later original receipt for the **same exact contract** with invalid book/size or stale venue event can invalidate that observation, yet the previous valid row remains counted. This is a false-positive causal source and held-contract coverage risk, not an alpha opportunity.

## Fixed change
1. For each day and eligible exact contract, keep the status of the **last original arrival-ordered receipt** (including invalid/stale). Set the day continuity bit only if that final receipt is valid and fresh. Keep the existing explicitly weak daily *market* presence counter unchanged; do not relabel it as a tradable mark.
2. For Sunday before Monday 00:00 UTC, the final original receipt of an eligible exact contract controls entry: a later invalid/stale receipt revokes its prior valid <=300-second causal quote. Preserve original event/arrival causality and <=1-second cross-leg skew.
3. Independently reconstruct the same decision from raw hashed original bytes without importing the primary module. Adversarial CI: a later invalid Sunday receipt removes a formerly causal pair (1 -> 0); a later invalid Monday receipt removes same-contract continuity (1 -> 0). Original valid control stays 1; forged counts fail the independent oracle.
4. Do not change strategy, economic gates, parameters, license status, paper, Frozen, legacy champion, sealed validation [2023-10-01,2024-01-18), or holdout >=2024-01-18. All synthetic counts remain **NOT** native economics, execution, settlement or ROI.

**Pass gate:** GitHub CI success on this branch with independent original-byte reconstruction, negative and positive controls. **Fail gate:** leave SOURCE_ONLY/HOLD and no promotion; no execution on real capital. The actual licensed BTC/ETH Deribit option BBO+sizes+original event/arrival archive and dated fee/margin/settlement receipts remain external.
