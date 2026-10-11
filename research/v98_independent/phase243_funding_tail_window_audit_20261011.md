# V98 Independent Phase243 — training-only funding tail diagnostic (2026-10-11)

Branch: research/v98-independent-zero. Scope: V98-only Phase206 native funding, 2023-01-01 through 2025-12-31. This is an ex-post DATA-ONLY risk audit, NOT strategy PnL or a candidate selection gate. Holdout remains untouched; V16/V99 untouched.

Across five native 8h settlement series, 3,288 aligned training slots per asset passed chronology and 0..29ms jitter checks. Two independent rolling-window algorithms (floating rolling sum and integer fixed-point prefix sum) agreed on all fixed 3, 6 and 21-settlement extrema.

Most negative signed SOL 21-settlement sum: -390.8328 bp (2023-01-01 00:00 to 2023-01-07 16:00 UTC); SOL 6-settlement minimum -276.2478 bp, SOL 3-settlement minimum -209.7102 bp. BNB 21-settlement minimum -223.1714 bp (2023-03-17 00:00 to 2023-03-23 16:00 UTC). These are per-unit-notional raw funding sums for hypothetical continuously held long exposure; not compounded portfolio returns and not adjusted for price drift, fees or trading.

BNB has 1,800 zero-funding training slots; 16 coincide with >7bp absolute funding on at least one other asset, 6 with >14bp. Zeros are NOT assumed erroneous and must not be imputed or selected as alpha features. XRP 2023-11 monthly 1h remains rejected due a single 2023-11-14 11:00 UTC physical quote/base inconsistency. No Phase243 alpha or champion promotion.

Source files must be independently authenticated before any promotion. Separate daily 1m/1h XRP originals are still missing; V98 research remains BLOCKED_SOURCE_CONFLICT. No parameter tuning or source repairs were performed.
