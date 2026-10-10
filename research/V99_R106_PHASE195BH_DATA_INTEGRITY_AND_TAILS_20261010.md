# V99 R106 Phase195-BH — 2026-10-10 forensic decision

Status: DATA_ONLY/HOLD. No promotion, no PnL replay, no holdout read. V16 Frozen, V99 Frozen, paper-results, dashboard and champion unchanged.

Official runs 38041119351 and 38041870546: all eight candidate paper histories differ from the published prefix at 2026-10-01 16:00 UTC. Seven full ledgers show funding-shaped differences of -R$0.05 to -R$0.49 with gross trading and fees stable within rounding. V99 compact has -R$0.36 but lacks funding attribution. This is NOT authenticated evidence of late funding; provider receipts are absent. All candidate shared hours across these two runs are stable. Publication remains blocked.

V15: 127 dynamic symbols; all 127 have eligible-after times earlier than conservative first complete hourly candle after discovery receipt. ERAUSDT added, PIXELUSDT removed, nine existing symbols re-discovered. 191 observed dynamic adjustments show no premature action in the capped decision sample. This does not certify full PIT safety.

Research paper ZIP comparison 2026-10-10 00:00 -> 05:00 UTC: F1/F3 rewrote 447 overlapping equity hours, 1282/1375 comparable operation records, and 55/94 pre-paper backtest days. R98/F7/F12 each rewrote one final shared hour (00:00 UTC) by R$0.05. All five backtest reference curves misclassify 25 post-paper points. Full operations history is capped at 1500 rows.

Same-window descriptive paper: R98 +3.8777% / max DD -14.7626%; F1 +12.3391% / -14.7844%; F3 +16.4106% / -13.7608%. Ex-post best 72h block explains 145.1% of F1 and 117.7% of F3 log-excess growth versus R98. NOT a validated performance comparison.

Local independent tools and 22 unit tests passed (funding boundary 10, paired tails 8, PIT escrow 4); SHA-256 inputs and reports archived in Phase195-BH evidence bundle.

Preregistered next step: authenticated immutable raw OHLC/funding receipts, first-seen arrival timestamps, complete uncapped decisions and frozen input hashes. Then paired causal four-arm replay (baseline, PIT-only, funding-only, both) with t-1, train-only temporal folds, severe/supersevere costs, regimes, benchmark envelope and untouched holdout. Never repair published prefix in place.
