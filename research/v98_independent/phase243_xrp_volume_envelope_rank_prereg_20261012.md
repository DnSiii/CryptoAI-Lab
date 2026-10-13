# V98 Independent Phase243 — XRP physical-volume envelope and rank stability (preregistered)

Date: 2026-10-12 21:43 BRT. DATA_ONLY / NO_ALPHA. Training-only Binance USD-M XRPUSDT 1h November 2023 original monthly ZIP, pinned SHA256 `29b7a4a3b9360f7b3be131af6b1fd619f18e7344eea99b5c964e955e667027a7`. This study never reads holdout, V16 or V99; no repairs or model selection.

## Frozen diagnostics before computation
1. Verify exact archive SHA256, 720 chronological 1h bars, strict OHLC and taker-side physical constraints; quarantine any invalid rows, do not replace data.
2. For each anomalous hour, calculate conditional **total quote interval** [base*low,base*high], **buyer quote interval** [buy_base*low,buy_base*high], and **seller quote interval** [(base-buy_base)*low,(base-buy_base)*high]. Condition: original base-volume fields and OHLC are accurate; otherwise intervals are not truth claims. Identify if observed buyer quote is feasible and if observed seller quote is feasible, without assuming which source field is wrong.
3. For full within-month trailing 1h, 24h, 168h quote-volume windows, compute observed window sums and **rank sensitivity** under all possible corrected total quotes in the physical interval, holding other hours fixed. Competition rank = 1 + number of window sums strictly greater than the target. Report min/max attainable rank for each affected window and largest shift from observed rank. Rank endpoints are computed at interval boundaries, not optimized against returns. No alpha or performance metrics are used.
4. Compute monthly total quote-volume interval and anomalous-hour share interval, conditional on the same fixed-base assumption. Do not extrapolate outside 2023-11. Preserve source and derived evidence SHA256; reject if any unexpected defect, invalid source, or unbounded field is encountered.
5. Independently test rank calculations against brute-force endpoint recalculation, chronological contamination causality, deterministic repeatability, source hash pinning and rejection of malformed sources. Tests cannot authenticate exchange data.

## Decision
Data-only: physical inconsistency or rank instability => SOURCE_QUARANTINE; even zero rank shift does not clear the source. Require independent daily 1h/1m originals with verified provider sidecars and external independent provenance before releasing Phase243. No cherry-picking, holdout opening, source patch, champion promotion or Phase240 rescue.
