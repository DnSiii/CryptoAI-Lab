# V98 A2 — preregistration before economic results (2026-11-08)
Status: UNVALIDATED, NOT PROMOTED. A0 and A1 remain rejected.

Hypothesis: cross-sectional relative strength rotation among authenticated Clean-4, with weekly decisions, will reduce A1's persistent exposure to weakening assets and trading churn while retaining upside participation. This is a genuinely distinct portfolio-selection mechanism, not a threshold rescue of A1.

Universe: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, Binance USD-M 1h; December 2022 warmup to December 2025 only. Native V98 funding. XRP quarantined. No 2026+ or contaminated Phase083 holdout. No external engine parameters or results.

Fixed architecture: (1) Growth Core: rank-1 0.22/rank-2 0.12; (2) Opportunity Sleeve: +0.06 if weekly return exceeds quarter of 720-hour return; (3) Relative-Value Sleeve: +0.06 on rank-1; (4) Stress/Recovery Sleeve: +0.04 on eligible asset with 336-hour drawdown between -20% and -7%; (5) Regime Router: halve if 168-hour hourly RMS log return exceeds 0.035; (6) Dynamic Allocator: cap total at 0.75; (7) Risk Governor: per-asset cap 0.40. Rank top two only if 720-hour and 168-hour returns both positive. Weekly rebalance at i % 168 == 0. Deterministic alphabetical tie break. Slots from hour t execute at next hour's open. No hidden leverage.

Predeclared gates: full authenticated 27048-hour replay with native funding, normal 4+2 bps costs and 2x/4x stress; calendar-year consistency, maximum drawdown, tails, concentration, positive days, PF and reproducibility. Chronological train/validation folds must be defined before candidate promotion; no promotion from in-sample replay alone. Rejection if normal CAGR <=0, 2025 net negative, 4x net negative, or any source/causality failure. If rejected, do not alter signs, windows, thresholds or costs to rescue it.

A2 is a research hypothesis, not a trading recommendation. No PnL has been observed at registration.
