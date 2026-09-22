# V99 R106 Phase114 — USD-M bookDepth availability/integrity audit preregistration

Pre-registered after Phase113 permanent rejection. Phase114 is **DATA/INTEGRITY AUDIT ONLY** and is not an alpha experiment.

## Motivation
Phases64–111 exhaustively tested OHLCV-adjacent and Binance futures-metrics families; Phase113 tested continuous premium level and failed decisively. The official Binance USD-M public archive also exposes a distinct `daily/bookDepth` family containing timestamped depth/notional bands around the market. This is genuine order-book/liquidity-state information rather than another transformation of return, funding, open interest, taker flow, positioning, or premium.

No order-book alpha is permitted until coverage, schema, sampling cadence and integrity are measured independently.

## Frozen audit contract
- Canonical PIT48 symbols only.
- Relevant research window: 2021-12-01 00:00 UTC through registered train end 2024-01-18 00:00 UTC.
- Source only official `data.binance.vision/data/futures/um/daily/bookDepth/<SYMBOL>/` ZIPs and matching checksum files.
- Directory/object-name metadata may be used only to identify pre-train files; **no post-train archive content or market value may be downloaded or parsed**.
- Inventory per symbol: first/last admitted train date, observed files, expected files within its admitted span, explicit missing dates and coverage ratio.
- Deterministic integrity sample: first available admitted archive of every calendar quarter for every symbol.
- For sampled files validate SHA256, ZIP CRC, nonempty CSV, schema/header, parseable timestamps, finite percentage/depth/notional, nonnegative depth/notional, unique (timestamp, percentage) rows, and monotone nondecreasing timestamp order.
- Inventory distinct depth-percentage bands and empirical timestamp cadence from the sampled files; do not assume a cadence or band set in advance.
- Missing archives/rows remain missing. No fill, interpolation, inference or synthetic book reconstruction.
- Do not compute returns, future returns, PnL, candidate weights, regimes, benchmark comparisons, predictive correlations or sign/direction.

## Decision
Phase114 may report only data availability/integrity facts. Any later bookDepth alpha requires a separate post-audit preregistration fixing one economic mechanism, transformation, direction, horizon and causal lag before any PnL.

V16 Frozen and V99 Frozen remain immutable. Holdout market values remain untouched.
