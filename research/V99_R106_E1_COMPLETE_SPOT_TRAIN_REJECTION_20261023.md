# V99 R106 E1 — original OKX spot-only complete TRAIN, independent economic rejection (2026-10-23)

**DECISION: E1 PERMANENTLY REJECTED, NO RETUNE. DATA_ONLY/HOLD — NO PROMOTION.**

E1 is a single preregistered **distinct** spot-only strategic BTC/ETH risk-premium engine, not a resurrection of C1/C2/D1, breakout or weekly cross-sectional rotation. Fixed 45% BTC / 45% ETH / 10% cash, rebalanced monthly, no leverage or perp funding. The rules and ten named requirements (nine numerical gates plus independent source/accounting completeness) were preregistered **before** reading E1 returns at commit [d98632b](https://github.com/DnSiii/CryptoAI-Lab/commit/d98632b91a6ffaf5d9ef6012d47de6a298c03870). Later clarifications only fixed ex-ante 3x2 regime boundaries before economic CI.

## Real work, independently verified
- [GitHub Actions 40035624149](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40035624149): full first-party original-OKX 15,864-hour TRAIN replay, two fee+slippage scenarios and two additional stress scenarios, monthly self-financing spot/cash journals, three passive benchmark envelopes, risk/tail/fold gates, independent hourly original-price-to-cash ledger oracle; **successful**.
- [GitHub Actions 40035956976](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40035956976): re-executed the same preregistered TRAIN, independently recomputed the **three original-price buy-once benchmark envelopes and every economic pass/fail gate**, and tested an injected cash-corruption negative control. **Successful**. Intermediate failed CI runs were **software debugging only**, not economic strategy retunes; no rules, weights, cost parameters or partitions were changed.
- The two primary scenario hourly journal hashes (SHA-256) are severe `ba254c62e9db3fdf0aaa2faeb0201a23db318d526928efa8a17f5ec4538d1efc` and supersevere `633bd365b56f0489c93121fd37bd168fac369d7ccb956b6aa173e391b0b5c1b6`. The full journals, independent oracle and report are retained in artifact `v99-e1-original-spot-complete-train-40035956976` (artifact 12537316270).

## Pre-committed economic TRAIN results — SIMULATED, NOT EXCHANGE-CERTIFIED

| Metric | Severe modeled 0.12% per side | Supersevere modeled 0.24% per side |
| --- | ---: | ---: |
| Total compounded ROI | **-48.2867%** | **-48.3896%** |
| Positive chronological folds | **1/5** | **1/5** |
| Folds 1–5 ROI | -21.677%, -43.980%, -14.067%, +41.553%, -2.929% | -21.691%, -43.999%, -14.085%, +41.542%, -2.939% |
| Maximum drawdown | **-68.0837%** | **-68.1272%** |
| Daily profit factor | 0.94425 | 0.94412 |
| Return after removing best day | -53.943% | -54.035% |
| Worst daily return | -13.934% | -13.934% |
| Worst 7-day block return | -25.285% | -25.285% |
| Number of monthly allocation events | 22 | 22 |

Additional adverse execution-shock modeled ROIs: severe with extra 1% per-side penalty **-49.1363%**; supersevere with extra 2% per-side penalty **-50.0660%**. The primary cost scenario returns degrade monotonically as modeled costs rise; independent self-financing accounting, fees, slippage, turnover, fold boundaries and native original-spot open prices reconciled for all hours.

The **buy-once, never-rebalance 45/45/10** benchmark returned -49.0418% supersevere. E1 monthly rebalancing improved that passive result by **only 0.6522 percentage points**, below the preregistered +2pp requirement. The original-price BTC-only and ETH-only passive benchmarks were independently checked analytically; no benchmark was selected after observing performance.

**Eight of nine numerical gates failed**: both ROI signs, severe >=4/5 folds, supersevere >=3/5 folds, max drawdown >=-35%, daily profit factor >1, remove-best-day positive, and supersevere improvement over fixed passive benchmark >=2pp. Only worst-day >=-15% passed. The independent source/accounting verification passed, but cannot rescue the economic rejection. E1 is **not** a superior trading engine.

## Limits, safety and next actual critical path
- Historical market opens came from 636 original first-party OKX HTTP pages verified before this experiment, **not actual account fills**. Account-specific 2021–2023 fee tier/lot/execution receipts are unavailable; modeled 0.12%/0.24% per-side costs do **not** authenticate exchange execution. There is no funding because E1 owns spot only. No realized account profit or forward paper ROI was claimed.
- Original TRAIN only: [2021-12-09, 2023-10-01). Sealed validation [2023-10-01, 2024-01-18) and final holdout >=2024-01-18 **unopened**. No real orders. V16 Frozen, V99 Frozen, paper/results and legacy champion **unchanged**. Do not publish the rejected E1 as an improvement.
- Do not retune E1 after observing these losses. C1, C2 and D1 also remain rejected. The evidence now shows three different complete economic mechanisms (directional trend, contrarian beta, spot passive beta) and a basis-carry entry prerequisite failing, not an investable superior V99.
- Next work must be **mechanism-first** rather than serial price-signal threshold grids: establish an independent, falsifiable, source-covered reason for positive after-cost expectancy that survives a bear market, then preregister ONE complete architecture with native fee/settlement and execution modeling, original TRAIN 5 folds and independent gates. Historical hypothetical fills cannot be authenticated retroactively; obtain the applicable account fee schedule and exchange instrument lot metadata or keep execution explicitly conservative and **block promotion**. Do not inspect validation or holdout until a new candidate actually passes TRAIN and is frozen.
