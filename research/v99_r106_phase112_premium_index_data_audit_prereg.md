# V99 R106 Phase112 — premium-index kline availability/integrity audit preregistration

Pre-registered while Phase111 is still running. Phase112 is a **DATA/INTEGRITY AUDIT ONLY**. It is not an alpha candidate and must not compute any relation to future returns, PnL, regimes, V99, or benchmark outcomes.

## Motivation
The official Binance public-data archive exposes USD-M `premiumIndexKlines`, a market-state family distinct from OHLCV, funding-event history, taker-flow aggregates, open-interest, and long/short positioning already studied in earlier R106 phases. The premium index measures the perpetual premium component used in the futures mark-price/funding machinery and can support a later basis/carry hypothesis only after availability and integrity are established independently.

## Frozen audit contract
- Source only official `data.binance.vision/data/futures/um/daily/premiumIndexKlines/<SYMBOL>/1h/` archives and matching `.CHECKSUM` files.
- Universe: canonical PIT48 manifest only.
- Time: list/admit files only through the already registered train end **2024-01-18**. Do not request, list for analysis, download, parse, summarize, or otherwise inspect holdout observations.
- Inventory per-symbol first/last date, observed/expected files, explicit missing dates, and coverage ratio.
- Deterministic integrity sample: first available archive of every calendar month per symbol; validate SHA256, ZIP CRC, nonempty CSV, 12-column kline row shape, parseable/monotone/unique open timestamps, finite OHLC values where present, and symbol/date path consistency.
- Do not forward-fill or infer unavailable dates. Missing archives remain missing.
- Do not compare premium values with returns, future returns, candidate PnL, regimes, benchmark metrics, or any prior winning/losing alpha.
- Phase112 may only answer whether this source is sufficiently available and structurally valid for a later separately preregistered experiment.

## Decision
`DATA_AUDIT_COMPLETE` only if the audit itself completes and records all discovered gaps/schema/integrity facts. Any later premium/basis alpha requires a **new preregistration after Phase112 evidence exists**, with one fixed direction/transformation/horizon before any PnL is observed.

V16 Frozen and V99 Frozen remain immutable.
