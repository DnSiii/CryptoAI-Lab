# V98 NX — preregistered seven-slot trend/carry/volatility portfolio (2026-10-30)

**New economic hypothesis:** persistent BTC market-direction participation + volatility-expansion opportunity + cross-sectional *funding carry* + always-eligible bear/recovery sleeve. This is NOT a rescue of NW/NV or any rejected engine: no NW source/threshold/window/sign is altered; new economic mechanisms and funding-based RV. Frozen before any NX historical PnL.

**Universe/time:** Clean-4 BTC/ETH/BNB/SOL Binance USD-M hourly, Dec 2022 warmup, Jan 2023–Dec 2024 development. 2025 previously exposed; not independent validation. Never access 2026+ holdout or quarantined XRP. Native 8h funding rates, conservative authenticated mark envelope (not exact event mark).

**Calendar and physical:** 53 14-day decisions at t=744+336k, signals only through close t, fill at open t+1. One-way netting, signed funding and all-hour carry, no hidden leverage. Exact 30-cell economic and physical gates identical to the previously preregistered NW gate; no post-result rescue.

**Seven slots:**
1. Growth Core: if BTC 336h return >0 and at least two of four assets have positive 168h returns, long BTC +0.62 and strongest non-BTC 168h return (if positive) +0.18. Otherwise short BTC -0.62 and weakest non-BTC 168h return (if negative) -0.12. Fixed maximum core gross 0.80.
2. Opportunity: select asset with greatest absolute 24h log return; when |r24| >0.025 and r24 and r72 have same sign, take directional +0.18 or -0.18. Otherwise zero. Volatility expansion / continuation, not a high-price breakout or volume rule.
3. Relative Value: average *past* 21 funding events per asset, long lowest mean funding and short highest mean funding +0.12/-0.12 if the spread >0.00001; otherwise zero. Signed carry, no beta estimation or price residual.
4. Stress/Recovery: when BTC 168h return <0 and BTC 24h return <0, short BTC -0.18; when BTC 168h return <0 and BTC 24h return >0, long BTC +0.12; when BTC 168h >=0 and BTC 24h return <-0.04, short BTC -0.18; else zero. Active defense/recovery in bearish conditions.
5. Regime Router: risk-on iff BTC 336h return positive and >=2 positive 168h asset returns. Risk-on multipliers Opportunity 1, RV 0.7, Stress 0.4; risk-off Opportunity 0.8, RV 1, Stress 1.
6. Dynamic Allocator: existing preregistered V98 causal net-growth 27-action (0/.5/1 per optional sleeve) allocator with 336h return, 21 historical funding events, fixed 168h horizon, virtual gross <=.84.
7. Risk Governor: existing signed atomic pretrade projection, carried-before-fill and new-after-fill funding order stress, hard physical gross <=.90, intrabar solvency and all-hour checks.

**Fixed pass/fail gates:** 5 ablations x 3 cost tiers x 2 funding order = 30 physical cells; costs base 4+2 bps, severe 10+10 bps, supersevere 15+20 bps. Base CAGR >80%, severe >60%, severe max DD <45%, severe 2023 and 2024 positive, turnover <=$600k per $10k initial; Opportunity, RV, Stress marginal net log-growth >0.02 and each annual marginal >=-0.03. These are minimums, not ceilings. All independent source, hourly accounting, fill and 30-cell arithmetic gates mandatory. Failure means permanent rejection.

**Independence:** V14/V15/V99 signals and internals prohibited; 2025 not fresh validation; future holdout untouched; no live or paper authorization.
