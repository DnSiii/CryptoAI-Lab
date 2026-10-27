# V99 I1 — independent expiry-state invariant (pre-implementation, 2026-10-27 12:xx BRT)

**Scope:** independent `research/verification/independent_v99_r106_i1_native_coin_account_oracle.py` and negative controls only. No strategy change, no data or economics, no frozen/paper/holdout/orders.

**Identified independently of PnL:** the independent reference presently permits a `mark` at or after the position's contractual expiry, permits a `nav` while an earlier contract remains unsettled, and permits a `settle` of a later contract while an earlier contract is still open. The primary native wallet rejects expiry-invalid marks and unsettled earlier expiries. These oracle discrepancies could make a self-consistent forged historical journal appear valid even though actual native expiry/delivery losses are omitted.

**Fixed ex-ante correction:** (1) reference `mark` requires `t < expiry_ms`; (2) `nav` with open positions requires every expiry `>= t`, and on exact expiry requires settlement first (strict `expiry_ms > t`); (3) `settle` forbids any other open position with earlier expiry. Do not alter any other economics, rule, portfolio path, threshold, or input.

**Verification:** add adversarial unit tests for all three cases on severe and supersevere, plus existing positive two-position/mixed-expiry independent replay; run actual GitHub Actions triggered by code push; report only software integrity. No historical economic TRAIN and no promotion unless original licensed lifecycle and native terms independently verified.

**Gate:** if CI fails, correct and rerun; never treat tests as real performance. SOURCE_ONLY/HOLD — NO PROMOTION.
