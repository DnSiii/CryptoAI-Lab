# V98 Independent — Phase224 funding provenance correction

Status: **CORRECTION — DATA BLOCK REMOVED; HOLDOUT STILL CLOSED**

The prior assessment that V98 lacked realized funding was incorrect. The V98-only snapshot `research/v98_independent/data/phase206_funding/` is an official Binance USD-M **monthly fundingRate archive**, not a premium-index/forecast substitute.

Evidence checked before any Phase224 alpha result:
- `manifest.json` identifies `https://data.binance.vision/data/futures/um/monthly/fundingRate` as the source, mode `DATA_ACQUISITION_ONLY`, requested through 2025-12, with `holdout_opened=false` and `alpha_or_pnl_computed=false`.
- `integrity_audit.json` reports `transport=official_binance_archive`, status PASS, and last observations strictly before 2026-01-01 for all five assets.
- Canonical CSVs contain `fundingTime_ms`, `fundingTime_utc`, `fundingRate`, `fundingIntervalHours`; e.g. BTC starts with settlement timestamps and 8-hour intervals.

Scientific disposition: Phase224 may use these rows as realized settlement observations, subject to its preregistered rule that a funding observation can enter the signal only after its timestamp (`fundingTime < decision_time`) and any settlement crossed while a position is live is charged/credited PIT. No forecast/premium field may substitute for `fundingRate`.

This correction changes **data availability/provenance only**. It does not alter the frozen Phase224 hypothesis, 8 specs, folds, costs, gates, or 2026+ firewall. No Phase224 result was observed before this correction.