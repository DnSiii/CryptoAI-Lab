# V98 NW — preregistration before any NW physical PnL (2026-10-30)

**Hypothesis:** a price-structure-driven, seven-slot composed engine using trend leadership, volatility breakouts, cross-sectional residual reversal and drawdown recovery is economically distinct from NV volume migration. This is a **new candidate**, not a rescue of rejected NV/NO/NS/NT. The primary target is compounded wealth subject to hard survivability and causal execution.

**Data:** Clean-4 BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT Binance USD-M hourly. Only 2022-12 warmup and 2023-01 through 2024-12 development. 2025 is previously exposed and is NOT independent validation; 2026+ holdout remains untouched. XRP quarantined. Native funding rate and event calendar, conservative signed official hourly mark envelope, never falsely called exact event mark.

**Fixed 14-day decision calendar:** t=744+336k, t < 18,288; signal from OHLC ending t; order at t+1 open; 53 decisions. No intraperiod target changes except causal inventory risk governor.

Seven slots:
1. Growth Core: 336h and 168h log-return positive and close above 168h average; rank eligible by 336h momentum, long top +0.72 and runner-up +0.08. If no eligible and BTC 168h return <-0.04 and BTC below its 336h close average, short BTC -0.52. Otherwise cash.
2. Opportunity: prior-168h breakout (current close exceeds max high of t-168..t-1), 72h return positive and realized 72h range compression versus preceding 168h (mean (high-low)/close in last 72h < 0.90 of preceding 168h); long eligible highest 72h return +0.18. No future bar.
3. Relative Value: cross-sectional 72h BTC-beta residual reversal, beta estimated from last 336 hourly close log returns, clipped [0,2]; select among ETH/BNB/SOL highest and lowest residual; if spread >0.035, long lowest residual +0.12, short highest residual -0.12; zero otherwise. Cross-asset pairs not reused from rejected engine.
4. Stress/Recovery: BTC drawdown from 336h previous high >0.12 and 24h return >0.015 -> BTC recovery long +0.18; otherwise drawdown >0.12 and 24h return <-0.07 -> BTC crash short -0.18; else zero.
5. Regime Router: BTC 168h return >0 and >=2 assets with positive 168h return defines risk-on. Risk-on multipliers Opportunity 1, RV 0.7, Stress 0.5; risk-off Opportunity 0.65, RV 0.8, Stress 1.
6. Dynamic Allocator: fixed existing causal net-growth capital-competition 336h/21 funding observation engine, 27 optional combinations 0/.5/1, 168h horizon, capped virtual gross .84; no realized future data or post-result adjustments.
7. Risk Governor: existing physical causal projection/atomic one-way netting, all-hour carried inventory, pre/post funding gross limits and intrabar survival, signed 8h funding, 0.84 intent gross and <=0.90 physical gross. No hidden leverage.

**Economic gates frozen now:** same as NV: 30 physical cells = 5 ablations x 3 costs (base 4+2 bps, severe 10+10 bps, supersevere 15+20 bps) x 2 funding orders; base CAGR >80%, severe >60%; severe max drawdown <45%, every severe calendar year positive, turnover <=$600k per $10k capital; each sleeve marginal log-growth >0.02 and annual marginal >=-0.03 in both years. These are acceptance floors, not upside ceilings. All cells must pass causal execution invariants. Failure => permanently reject NW without post-result rescue.

**Independent evidence:** independent source indicator recomputation, independent hourly signed accounting, independent fill reconstruction and tamper test, independent 30-cell arithmetic/economic gate; immutable receipt. A pass is *provisional training only* until independent chronological validation and future holdout. Do not inspect V14/V15/V99 for tuning. No live/paper authorization.
