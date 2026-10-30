# V98 Independent Phase244 — Clean-4 Time-Series Breakout Growth Core

Status: PREREGISTERED BEFORE PNL.

Phase244 is the first economic module of the reset V98 architecture: Growth Core. It is a persistent per-asset time-series state machine, distinct from the rejected cross-sectional residual/momentum and short-horizon volatility-compression families.

Frozen data: only Phase243 Clean-4 authenticated BTCUSDT, ETHUSDT, BNBUSDT and SOLUSDT; Binance USD-M 1h originals from 2022-12 warmup through 2025-12; native V98 funding; XRP remains quarantined for source integrity. No 2026+, V14, V15 or V99.

Frozen single specification, decision after close(t), execution open(t+1):
- entry channel = prior 90 days / 2160 hourly closes, excluding close(t)
- exit channel = prior 30 days / 720 hourly closes, excluding close(t)
- flat -> long on upside 90d breakout
- flat -> short on downside 90d breakout
- long -> short on opposite 90d breakout; otherwise flat on downside 30d exit
- short -> long on opposite 90d breakout; otherwise flat on upside 30d exit
- otherwise state persists
- each active asset = 25% absolute portfolio weight
- dynamic gross = 0..1.00 from breadth; no leverage scaling
- no stops, take profits, vol target, regime filter, parameter grid, sign flip, asset selection, threshold rescue, or post-result tuning

Execution uses the existing causal V98 exact stateful backtester and max open gross 1.0.

Existing V98 cost/funding tiers:
- BASE 7 bp/side; funding debit/credit 1.00x/1.00x
- SEVERE 12 bp/side; 1.25x/0.75x
- SUPERSEVERE 20 bp/side; 1.75x/0.50x

Training only on chronological 2023/2024/2025. Report return, CAGR, DD, daily PF, payoff, win rate, positive days, tails, turnover, fees, funding, exposure, asset concentration and regimes.

Growth-Core promotion gate:
1. BASE total return > +100%
2. BASE CAGR > 25%
3. BASE daily PF > 1.10
4. BASE max DD >= -45%
5. BASE worst day >= -20%
6. at least 2/3 calendar folds positive
7. worst fold return > -25%
8. SEVERE total return > +50% and PF > 1.05
9. SUPERSEVERE return > 0 and PF > 1.00
10. no ruin
11. max open gross <= 1.000000001
12. max absolute asset contribution share <= 70%
13. top-10 absolute daily-return concentration <= 40%

Pass => GROWTH_CORE_CANDIDATE only. Failure => REJECT_GROWTH_CORE_NO_RESCUE for this exact 90d/30d rule. No validation or holdout is opened by Phase244.
