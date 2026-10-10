# V99 R106 Phase195-BJ — immutable publication firewall (2026-10-10)

**Decision: DATA_ONLY/HOLD.** No new validated champion, no promotion, no holdout use. V16 Frozen, V99 Frozen, main, paper-results and dashboard must remain untouched by this research commit.

## Fresh official evidence

At 2026-10-10 11:16–11:28 UTC, official runs 38047409793 and 38048129364 completed their simulation steps but failed **Verify published history was not rewritten**, specifically `Published equity_curve was rewritten; recovery publication blocked`. The subsequent run 38048853916 also reached the same failed verification step. This is a persistent integrity gate, not a healthy published forward update. The official automatic recovery loop must not be treated as successful paper publication.

## Independent reproducible local evidence

Compared archived durable V99 research ledger (2026-10-10 00:00 UTC) to run 38032784420 (05:00 UTC), 564 shared paper hours per variant. F1/F3 each changed 447 shared hours, beginning 2026-09-21 10:00 UTC; R98/F7/F12 changed the shared 2026-10-10 00:00 hour. F1/F3 also changed 78/117 backtest reference days. The newer ledger contains 25 forward-period timestamps in each displayed backtest reference. F1/F3 operations are capped at 1500, preventing a full immutable operation-prefix proof.

## Implemented protection

`scripts/v99_phase195bj_paper_publication_guard.py` reads the durable paper-results ledger from an explicit fetched commit, validates UTC/ordering/hourly continuity, the five shared-boundary paper prefixes, unchanged historical backtest reference, strict pre-paper labeling, uncapped operations, and no-real-order mode. The V99 research paper writer calls it **before any output files are written**. On failure it raises and prevents the downstream workflow publication step. The gate does not repair or rewrite any published row, does not authorize promotion, and fails closed when the durable ledger is unavailable. Independent offline CI tests exercise adversarial mutations.

## Next scientific step

Secure immutable source receipts (OHLC, funding, first-seen universe and uncapped operations), pin hashes and chronological train boundaries, then preregister and execute paired four-arm causal replay: baseline / PIT-only / funding-only / combined. Require t-1, untouched holdout, temporal folds, severe and supersevere costs, regime matrix, benchmark envelope, and anti-overfit gates. Do not classify DATA_ONLY exploratory ROI as a champion.
