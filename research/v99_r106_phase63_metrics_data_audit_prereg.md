# V99 R106 Phase63 — orthogonal futures-metrics availability audit

Pre-registered while Phase62 is still running; this is a **data/integrity audit only**, not an alpha candidate.

## Motivation
The Binance USD-M public archive has a separate daily `metrics` family containing open-interest and positioning/flow aggregates. This is structurally more orthogonal than another OHLCV transformation or a retune of rejected taker-flow continuation. Public Binance-data issue history also documents occasional missing metric dates, so no alpha hypothesis is permitted until coverage is measured rather than assumed.

## Audit contract
- Source only official `data.binance.vision/data/futures/um/daily/metrics/` archives and matching `.CHECKSUM` files.
- Restrict every request/parser to timestamps <= the registered train_end. No holdout metrics may be downloaded or parsed during this audit.
- Validate SHA256, ZIP CRC, symbol identity, timestamp monotonicity/uniqueness, finite/nonnegative open-interest fields where applicable, and explicit missing-date accounting.
- Inventory schema fields without evaluating their relation to returns, PnL, V99, regimes, or benchmark outcomes.
- Produce per-symbol first/last available date, expected/observed files, missing dates and coverage ratio. Do not silently forward-fill missing files.
- A later alpha study, if justified, requires a separate pre-registration after this audit. Phase63 itself cannot choose a feature, direction, horizon, threshold or candidate.

This audit cannot modify V16 Frozen or V99 Frozen.