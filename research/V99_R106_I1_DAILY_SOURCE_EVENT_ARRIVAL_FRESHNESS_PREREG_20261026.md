# I1 661-day original daily tape: preregistered clock/freshness correction (2026-10-26 20:50 BRT)

## Concrete critical-path defect
The original 661-day daily source-presence gate and its independent oracle currently reject a valid venue event from the previous UTC date if the original packet arrives shortly after midnight, because they enforce `day_start <= venue_event`. Tardis daily partitions are by **local arrival date**; this false negative can block a legitimate licensed archive. Conversely, a quote with arbitrarily old venue event but an arrival on the correct day currently counts as a fresh daily mark, potentially inflating the weak 182 asset-week presence count. Both errors matter before any full historical economic TRAIN.

## Frozen ex ante correction, no tuning
1. Source day is the **original local arrival UTC day**: `day_start <= local_timestamp < next_day_start`, ordered nondecreasing across the file. Original venue event must satisfy `0 <= timestamp <= local_timestamp`, but need not be on the same UTC date.
2. Count an option quote toward necessary daily presence **only** if `0 <= arrival - event <= 300,000,000 microseconds` (five minutes). The bound matches the existing 300s quote freshness gate, and is not fitted to historical PnL. A stale but chronologically valid event remains a source row and remains included in the hash/row count; it does **not** qualify as a mark.
3. Preserve exact original SHA-256, no duplicate/missing days, 661-day TRAIN-only partition, venue, monotonic arrival, quote shape, 182 weak asset-week presence schedule, and explicit `certified_complete_option_lifecycles=0`. Update independent oracle without importing primary module.
4. Add negative controls: prior-day event arriving just after midnight must be accepted; stale prior-day event must not count as daily presence; future event must reject; wrong arrival day must reject. Run GitHub Actions and verify independent replay, including the original 661-day synthetic fixture.

## Interpretation / safety
Daily presence is necessary, never sufficient for executable original same-instrument 21-45-day lifecycle; neither a green test nor 182/182 synthetic presence certifies exchange fills, native fees/margin, economic ROI, holdout, or promotion. Missing licensed 2021-2023 BTC+ETH full tape and native historical terms remain the external blocker. Never modify V16/V99 Frozen, champion, paper, orders, validation or holdout.
