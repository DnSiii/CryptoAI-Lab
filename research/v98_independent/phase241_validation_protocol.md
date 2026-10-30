# V98 Independent Phase241 — independent validation protocol

Expected frozen surface: exactly 4 specs; folds 2023/2024/2025; costs base/severe/supersevere. Every cell must contain return, max drawdown, Profit Factor, payoff, win rate, positive days, turnover, tail p01/p05/p50/p95/p99, funding contribution, per-asset PnL/concentration, and bull/bear/sideways diagnostics.

A spec may pass only if EACH annual fold has: base return > 0; base PF > 1; base max drawdown >= -35%; base positive days > 50%; severe return > 0; severe PF > 1. Supersevere 28 bp is mandatory stress evidence and cannot be tuned. Family decision is REJECT_FAMILY_NO_RESCUE when no frozen spec passes every annual gate; otherwise only frozen passing specs may advance.

Before accepting any decision, require a second deterministic execution with byte-identical result payload, verify cutoff <2026-01-01, monotonic/unique timestamps, gross <=1, lagged t-1 information, PIT funding, and exact frozen grid. No post-result sign flip, threshold search, asset deletion, regime filter, grid expansion, or V99-based selection.