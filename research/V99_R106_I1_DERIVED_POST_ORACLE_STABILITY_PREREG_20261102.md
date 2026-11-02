# V99 I1 — preregistered derived-byte stability gate (2026-11-02)

## Scope and reason
Source-only, sealed TRAIN 2021-12-09 through 2023-09-30. The 661-day CoinAPI source-chain runner independently replays original compressed partitions against derived gzip files. The previous original-partition post-oracle rehash does **not** establish that a derived daily gzip was unchanged between the independent oracle's return and the downstream daily scanner. A concurrent writer can replace the derived gzip with different prices and the scanner might still observe the same row count. This is a source integrity defect, not evidence of alpha.

## Fixed change, before implementation
For each day, require the sidecar's derived_gzip_sha256 to be a canonical lowercase SHA-256, hash the derived gzip before independent oracle replay, rehash it immediately after that replay and again after the scanner, and reject any difference with a distinct fail-closed error. Never reconstruct a missing original file, never use a derived gzip as original venue evidence, never alter the economic rules or historical partitions. Do not touch Frozen, paper, champion, validation or holdout.

## Negative control
In the existing full 661-day synthetic fixture, patch the independent oracle so that, **after** its first-day success, it rewrites that first-day derived gzip to another valid gzip with exactly the same row count but different prices. The runner must reject it before the daily scan; restored fixture must pass unchanged. Also reject a forged sidecar digest before independent replay.

## Decision criteria
GitHub CI must run the full 661-day source-chain test, show the post-oracle derived-byte negative control failing closed, and demonstrate the absent real license veto. Passing this test is **NOT** real original-source completeness, native fees/fills, economics, 5-fold profitability, freeze, promotion, paper or orders. Real economic TRAIN remains blocked on lawful original BTC/ETH 661-day archive and independently authenticated native execution/fee/margin/settlement receipts. No ROI is claimed.
