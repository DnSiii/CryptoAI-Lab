# Phase195-BI — recovered first-seen receipt audit (published 2026-10-10)

This read-only source-integrity tool was previously validated offline but not published. It is now preserved on the R106 research branch, with CI. It **does not** change V15, V16 Frozen, V99 Frozen, paper-results or dashboard.

Three official artifacts from 2026-10-10: runs 38043966853, 38044661910 and 38045334304. In each, 129 dynamic assets have eligibility timestamps earlier than their first recorded discovery receipts (minimum/median/maximum 60.68/104.56/1931.29 minutes). Twelve discovery timestamps changed between consecutive runs. The observed 191 dynamic adjustments show no early action in the capped sample, not a certification.

Root mechanism from `scripts/sync_paper_data_v15.py`: newly discovered symbols receive `discovered_at_utc=now` but `eligible_after_timestamp=verified_boundary` (a prior closed market hour). Failed official publication means restored universe state is stale, causing repeated rediscovery and new timestamps. A candle close is not proof of an earlier exchange-discovery receipt.

Gate: compare immutable per-symbol provenance across two artifacts, reject backdated eligibility, reissued/new symbols, missing receipts and premature observed adjustments. This is DATA_ONLY/HOLD pending authenticated immutable receipts, uncapped decisions, and paired causal replays. No holdout or promotion.
