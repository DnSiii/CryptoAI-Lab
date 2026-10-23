# V98 Independent Phase1114 — W structurally rejected before historical PnL

Date: 2026-10-23. Branch: `research/v98-independent-zero`. Scope: W-only files.

## Frozen facts
- Phase1110 256-state signed governor: 10/10 synthetic tests including 3,000 seeded adverse portfolios; no historical PnL.
- Phase1111 seven-slot W source: 7/7 synthetic tests; five paths, t+1 opening, no 2025+ or external benchmarks.
- Phase1112 signed stop-first ledger: 11/11 synthetic tests after implementing the preregistered 12h refresh (no hourly stop refills); no historical PnL.
- Official CI Phase1110-1112: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/39977464127 — PASS.
- Official complete W synthetic composition Phase1113: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/39977521159 — execution PASS, **decision REJECT_W_STRUCTURAL_SYNTHETIC**.
- Three fixed seeds (1113, 1114, 1115) x five W paths = **0/15 complete synthetic survival paths**. First failed hours were respectively 754, 728, 727, identical across the five paths for each seed. Failure code: `W_UNANTICIPATED_GAP_OR_RANGE`. The 2200h OHLCV series were SYNTHETIC, not authenticated market history. No CAGR, Profit Factor or historical performance was computed.

## Exact failure
W uses prior 336h max hourly adverse movement as a *hard future admissibility bound*. When an exposed asset makes a new adverse extreme, W rejects, even when a stop order could have executed at a worse but still tradable price. This is not a failure of the 256-state proof inside its fixed bounds; it is a failure of the composed executable portfolio in an open-ended price process. The 256-state proof and individual module tests do not establish full-system survival.

## Decision
**W_full STRUCTURALLY REJECTED before historical PnL.** W code, tests, preregistration and official receipts remain as immutable rejection evidence. No reselecting sign, window, threshold, gross leverage, fees or favorable seed. No W historical PnL, 2025, holdout, V14/V15/V99 benchmark inspection. A distinct X architecture must model *actual tradable emergency exits after previously unseen shocks* without declaring every new extreme a system failure or assuming an unrealistically perfect stop fill. Its actual post-execution equity, gross/net and tails must still pass. Growth/CAGR remains the objective; survival is a constraint, not an objective.
