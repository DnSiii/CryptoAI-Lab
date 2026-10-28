# V99 I1 — 661-day original tape parser hot-path optimization (preregistered 2026-10-28 20:5x BRT)

## Scope and frozen semantics
The full TRAIN 2021-12-09..2023-09-30 contains 661 daily gzip files. The existing importer parses a contract expiry with `datetime.strptime` and a strike with `float` for every put quote row; a single verified 2022-06-01 file has 14,720,180 rows, so repeated contract parsing is an avoidable scaling bottleneck. This is a **performance-only** change to source ingestion, not a new trading signal, parameter sweep, alpha candidate, or promotion.

Change only `research/tools/v99_r106_i1_local_tape_import.py::scan_day`: cache **immutable symbol-derived metadata** (asset, expiry, strike) per day with a bounded 32768-entry LRU. Continue to read **every original row** in arrival order, validate venue and clocks, recompute **every row's** bid/ask/size and staleness, scan gzip through CRC/EOF, hash the unchanged compressed original bytes, preserve 24/24 per-asset UTC-hour requirement and all existing manifest/economic vetoes. Never cache price, size, timestamp or validity by symbol. No changes to the independent oracle.

## Falsification and acceptance
1. Existing 661-day synthetic tests and adversarial malformed/stale/out-of-order/23-hour tests must pass without modified assertions.
2. Add a repeated-symbol test where an invalid latest quote follows a valid quote for the **same** contract; the invalid quote must never become valid because of cached symbol metadata. Include malformed symbol and both assets.
3. Run the **real unchanged** public Tardis Deribit 2022-06-01 gzip in GitHub Actions, independently replay the entire raw gzip with the existing independent hourly oracle, and require exact pre-change source SHA-256 `9d7b1e62fb7f16648348154ebcece472461d3038c96e61ca7e96de4ce8adcdbd`, original row count `14720180`, valid put rows BTC `1778798` and ETH `3138873`, 24/24 UTC hours each. No assertion of speedup without measured elapsed timing.
4. If any real-data discrepancy occurs, reject/revert rather than weaken original data checks. Do not access validation >=2023-10-01 or final holdout.

## Boundaries
Only one original day is publicly verified. The 660 missing days, vendor gap attestation, historical native fee tiers, lot units, margin/liquidation, delivery, and conservative fill model remain blocking. 0/180 economically certified option lifecycles; **SOURCE_ONLY/HOLD — NO PROMOTION, NO ORDERS, NO ROI**. V16 Frozen, V99 Frozen, paper and champion remain untouched.
