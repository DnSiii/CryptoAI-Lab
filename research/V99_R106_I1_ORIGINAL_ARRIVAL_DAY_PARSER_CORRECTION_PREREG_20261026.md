# V99 I1 — original Tardis arrival-day parsing correction (preregistered 2026-10-26 19:47 BRT)

**SOURCE_ONLY/HOLD — NO PROMOTION.** This is a correctness repair to the already executed non-sample one-day original quote ingestion, not a new alpha/strategy, a proof of archive access, an economic TRAIN or an order path.

## Defect observed in code before implementation
- Tardis official datasets API states daily gzip files are partitioned by **local_timestamp (capture arrival)**, not exchange event timestamp. Current source parser incorrectly requires `DAY_START <= timestamp`, which can reject a legitimate prior-day exchange event captured just after UTC midnight. The existing preregistration requires only **local arrival inside selected day and event <= arrival**. Fix to enforce `DAY_START <= local_timestamp < DAY_END`, `timestamp <= local_timestamp`, nonnegative exchange time, and nondecreasing arrival, without falsely requiring event date to equal arrival date.
- The option-symbol regex uses an extra literal backslash in the optional decimal strike, wrongly excluding decimal strikes. Correct it while continuing to exclude malformed instruments.
- Distinguish *field presence* from *execution-fresh quotes*: a positive bid/ask/size with event clock more than 10 seconds before arrival is not eligible to count as a fresh two-sided quote. Record stale counts without leaking original rows; no claim of executable fill. This conservative threshold is fixed here, not tuned to PnL.

## Falsification and run acceptance
- Synthetic positive controls: BTC prior-day event arriving shortly after midnight; ETH same-day event; decimal strike option; all within 10s.
- Synthetic negative controls: arrival outside chosen day, future event, event older than 10s cannot count as fresh BTC/ETH source coverage, malformed symbol, missing asset. Original gzip SHA-256, byte/row limits, fee/holdout/paper/frozen quarantines remain.
- Publish parser + tests on **research/v99-r106-native-all-regime-engine**; run actual GitHub Actions source workflow, poll completion and inspect logs. If `TARDIS_API_KEY` remains absent, status must remain **BLOCKED_NO_AUTHENTICATED_ENTITLEMENT**, network requests=0 and economic TRAIN not run; do not mislabel synthetic test success as original market proof.
- Reference: https://docs.tardis.dev/downloadable-csv-files/api (daily split by local timestamp). No access to sealed validation >=2023-10-01 or final holdout, no orders or economic promotion.
