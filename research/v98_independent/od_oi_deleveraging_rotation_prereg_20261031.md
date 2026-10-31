# V98 Independent — OD OI-Price Deleveraging Rotation (preregistered before code/PnL, 2026-10-31)

## Scope and independence
New **OD** complete seven-slot architecture, economically distinct from rejected OC and all other frozen/rejected experiments. Training source: SHA-pinned Clean-4 Binance USD-M hourly 2022-12 through 2024-12, BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT only; authenticated native OI v2 artifact from run 40477513000 with 37 quarantined asset-days; native funding-rate archive plus conservative hourly mark envelope. No 2025, no 2026+, no XRP, no V14/V15/V99 signals or benchmarks, no old Phase083 holdout. Source OI is sampled at 23:55 of the completed hour and is available only after that hour closes; intents at close[t] execute at open[t+1].

## Frozen seven-slot hypothesis (not tuned after results)
(1) Growth Core: every 672h, among four assets rank positive 672h log-return with positive 168h return; long 0.54 first, 0.18 second. If no eligible asset and BTC 168h return below zero and at least three assets have negative 168h returns, short BTC 0.30. Core never requires OI, preserving availability during quarantines.

(2) Opportunity Sleeve: every 168h, **only** if all four assets have continuous native OI in [t-167,t], identify assets with positive 24h price log-return above +0.025, positive 24h OI log-change above +0.02 and positive 168h OI change. Rank by 24h price change times 24h OI change, long top one 0.18. No eligible candidate means zero.

(3) Relative-Value Sleeve: with same strict OI mask, rank altcoins by (168h price log-return minus 168h OI log-change). If max alt score exceeds BTC score by 0.08 and alt 168h price return positive, long that alt 0.10 and short BTC 0.10; otherwise flat. Zero-net dollar hedge is explicit, not a source of hidden gross leverage.

(4) Stress/Recovery Sleeve: with strict OI mask, if >=3 assets have 24h price decline below -0.035 and >=3 have 24h OI contraction below -0.025, short BTC 0.16; otherwise if BTC 168h return below -0.10, BTC 24h return above +0.025 and >=2 altcoins have positive 24h returns, long BTC 0.14; otherwise zero. These are mutually exclusive.

(5) Regime Router: when BTC 336h log-return >0 and at least three assets have positive 168h returns, multiply Opportunity by 1.0, RV by 0.75, Stress by 0.50; otherwise multiply Opportunity by 0.75, RV by 1.0, Stress by 1.0. OI-ineligible windows zero all three optional sleeves without interpolation or rescheduling.

(6) Dynamic Allocator: preserve core targets, scale optional sleeves pro rata to remaining gross budget min(0.30,0.84-core gross). If trailing 168h BTC hourly log-return volatility exceeds 0.05, halve optional budget. No future PnL or realized future funding used.

(7) Risk Governor: causal signed one-way net atomic planner and t-1 projection from V98 Independent, gross target <=0.84, hard post-funding cap 0.90, no hidden leverage, no trade on zero next-open volume, worst-side hourly mark funding envelope, both event orders and all-hour checks. Native fees/slippage base 4/2 bps, severe 10/10, supersevere 15/20.

## Binding training gates
30 physical cells = 5 books (full/core-only/three leave-one-out) x 3 cost tiers x 2 funding orders; independent all-hour settlement and fill reconstruction plus separate OI/source/allocator oracles. In base both funding orders CAGR >80%, severe >60%, turnover <=$600,000, severe max drawdown <45%, positive 2023 and 2024 severe returns. Each optional sleeve must improve full-system log growth >0.02 in base and severe, both event orders, and not damage any annual log growth by more than 0.03. PF, payoff, win-rate, positive days, tails, concentration, 2023/24 chronology and causal t-1 must be reported; no false claim of trade-level PF from hourly returns.

If source, structural, physical, economic or independent gate fails, **reject OD permanently without rescue**. A training pass is provisional only: 2025 is already exposed, 2026+ future holdout remains untouched, exact funding-event markPrice remains unresolved, and no live/paper trading is authorized. Do not infer superiority from training.
