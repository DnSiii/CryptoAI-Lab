# V98 Independent — Phase243 BNB funding source corroboration preregistration (2026-10-09)

**Status: PREREGISTERED_DATA_ONLY_NO_ALPHA / NO_CHAMPION.** Only `research/v98-independent-zero`, V98 namespaced data and 2022-12 through 2025-12 training/warmup. No 2026+ holdout, V16, V99 or external-engine tuning.

## Trigger and frozen evidence

The existing V98 Phase206 native `BNBUSDT_funding.csv` has Git blob SHA `6b46a2a911d85079f3ce4ec5bc8b1791febd397a`. Independently recounting the frozen 2022-12-01 to 2026-01-01 exclusive interval yields **3,381** scheduled settlements, **1,852** exactly-zero rates (54.777%), and a longest consecutive zero run of **77 settlements**, from 2024-07-03 16:00Z through 2024-07-29 00:00Z (last report +1ms). The underlying file also contains earlier 2022 records, which are excluded from this audit. Zero rates are not automatically missing or invalid.

## Predeclared independent test

1. Obtain Binance USD-M **original monthly funding-rate archives** for BNBUSDT over 2022-12 through 2025-12, with original bytes, archive member inventory, SHA256 and available provider CHECKSUM sidecars. Authenticate transport, schema, month coverage, and timestamps independently of the existing Phase206 native CSV.
2. Reconcile on the **scheduled 8h boundary** (allow reporting jitter 0–50ms), compare every numeric funding rate exactly at source precision, and report mismatch counts, direction, month, zero-run lengths, and any exchange schema change. Do not silently impute, forward-fill, or turn missing values into zero.
3. Any disagreement, incomplete archive, or unavailable independent source => **UNVERIFIED_SOURCE / NO_PROMOTION**, not a chance to pick the economically favorable series. Existing 7/14/28 bp cost tiers, signal weights, funding sign, and settlement convention remain unchanged.
4. This is a data-quality test only. Do not interpret the frequency of zeros as a profitable strategy. No PnL-based model choice and no 2026+ holdout access.

**Decision gate:** a source discrepancy must be resolved using provenance, not performance. A source match alone does not qualify any V98 candidate for promotion.
