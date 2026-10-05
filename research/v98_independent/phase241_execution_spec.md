# V98 Independent Phase241 — executable implementation contract

This contract is frozen before observing Phase241 performance and exists because executable-file writes are currently blocked by the integration safety layer.

Implementation must read only V98 training data with timestamps strictly before 2026-01-01, for BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT and SOLUSDT. It must require monotonic unique timestamps and quote-volume availability; funding must come only from the existing V98 PIT funding dataset.

For each frozen vw in {168,336}: compute log1p quote volume; its rolling median and rolling MAD must each be shifted one hour before use. Compute 24-hour price return. At open(t), use only abnormal-volume and 24-hour-return observations at t-1. Cross-sectionally z-score each feature, define score = z(abnormal volume) * -z(24h return), long highest score and short lowest score, k=1, equal-weight and dollar-neutral. Each signal persists for frozen H in {4,8}; overlapping signals are aggregated and normalized so gross exposure never exceeds 1.

PnL at hour t must use position held from t-1 against open-to-open return, charge PIT funding against lagged held exposure, and charge L1 turnover at exactly 7/14/28 bp for base/severe/supersevere. Evaluate only calendar folds 2023, 2024 and 2025.

Every spec/year/cost cell must emit compounded return, max drawdown, Profit Factor, payoff, win rate, positive days, L1 turnover, funding contribution, p01/p05/p50/p95/p99 hourly tails, best/worst day, per-asset PnL, max absolute asset concentration, and bull/bear/sideways diagnostics defined only from lagged BTC 168h return. Serialize deterministically and execute twice; payloads must be byte-identical before validation.

Mechanical validator: a frozen spec advances only when every 2023/2024/2025 fold has base return >0, base PF >1, base max drawdown >= -35%, base positive days >50%, severe return >0 and severe PF >1. 28 bp is mandatory stress evidence. If none passes, emit REJECT_FAMILY_NO_RESCUE. No sign flip, asset deletion, regime rescue, threshold search, grid expansion, V99 evidence or 2026+ access is permitted.