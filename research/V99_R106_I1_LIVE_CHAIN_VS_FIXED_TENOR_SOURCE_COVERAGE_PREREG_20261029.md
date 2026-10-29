# V99 I1 — daily feed presence must not require 21–45d eligible puts (pre-implementation 2026-10-29)

**Scope: source integrity only; no strategy, fee, allocation, TRAIN or gate retune. SOURCE_ONLY/HOLD.**

## Falsifiable defect
The licensed 661-day importer treats absence of 21–45-day two-sided BTC/ETH put books in any UTC hour as a gap in the entire original options feed, and rejects a day when either asset has zero such rows. This confounds a market-universe/tenor absence with missing captured bytes. Fixed I1 28–35d entry eligibility is a separate screen; a legitimately empty fixed-tenor universe must be represented as zero, never invented as a fill.

## Fixed correction, before implementation
1. Preserve existing 21–45d descriptive counts and 28–45d counts unchanged. Add separate per-asset live_original_put_quote_rows_by_asset and live_original_put_arrival_hours_by_asset based on strictly original valid two-sided, positive-size, nonstale Deribit BTC/ETH puts with contractual expiry after the capture day, irrespective of 21–45d tenor. Continue to reject wrong venue, futures, expired options, crossed/zero books, stale venue clocks, bad order, corrupted gzip and sealed days.
2. require_hourly_original_coverage checks the new live-any-tenor 24/24 per-asset mask, not the old 21–45d mask; still only a necessary, not sufficient, feed-coverage heuristic. Reject zero live puts for either asset. No implication of complete exchange universe, licensed vendor grant, native fee tier, fill or trading economics.
3. Synthetic adversarial tests: 24-hour live puts with expiries >45d and zero 21–45d rows pass transport presence while fixed-tenor counts remain zero; missing hour, expired-only, futures-only, crossed-only and stale-only still fail. No change to 90 fixed Monday intents, signal, expiry selection, margin, cost, NAV, fold edges or any economic output.
4. Execute existing dedicated GitHub CI for local import, verify actual pass/fail and downstream compatibility. If downstream requires 21–45d nonzero as source integrity, keep blocked and document rather than silently weakening trade eligibility.

**Hard limits:** no licensed 661-day source, no certified economic lifecycle, no TRAIN ROI, no promotion, no validation/holdout, no orders; Frozen, paper and champion untouched. This only prevents a false feed-gap conclusion when the market legitimately offers no desired tenor.
