# V99 R106 Phase116 — mark/index paired-kline availability/integrity audit preregistration

Phase116 is a **DATA/INTEGRITY AUDIT ONLY**, opened after Phase115 confirmed the official USD-M liquidationSnapshot archive is unavailable.

## Motivation
Official USD-M `markPriceKlines` and `indexPriceKlines` provide two synchronized price processes with long historical coverage. Their difference represents a derivative-versus-index dislocation source distinct from ordinary traded OHLCV and from directly consuming the premium-index series tested in Phase113. Before any basis mechanism is specified, paired availability and timestamp integrity must be established independently.

## Frozen audit contract
- Canonical PIT48 symbols only.
- Interval fixed to 1h for both sources.
- Research content window starts 2021-12-01 and ends strictly before 2024-01-18 00:00 UTC.
- Source only official Binance public-data daily archives:
  - `data/futures/um/daily/markPriceKlines/<SYMBOL>/1h/`
  - `data/futures/um/daily/indexPriceKlines/<SYMBOL>/1h/`
- Boundary-day 2024-01-18 archives are excluded entirely.
- Inventory per-source/per-symbol first/last admitted dates, observed files, explicit missing dates and coverage.
- Compute paired-date coverage only from object metadata; do not compute mark/index values, basis, returns or predictive relations in the coverage stage.
- Deterministic integrity sample: first paired admitted date of each calendar quarter per symbol. For both archives validate SHA256, ZIP CRC, 12-column kline schema/row shape, finite OHLC, strictly increasing unique open timestamps, and exact timestamp alignment between mark and index sample files.
- Missing files/rows remain missing; no fill or inference.
- No PnL, sign, horizon, threshold, candidate weights, regime selection, benchmark comparison, or holdout market values.

## Decision
Only if paired data has sufficient history for the unchanged >=3-valid-fold temporal gate may a later basis/dislocation hypothesis be separately preregistered. Phase116 itself cannot select a mechanism.

V16 Frozen and V99 Frozen remain immutable.
