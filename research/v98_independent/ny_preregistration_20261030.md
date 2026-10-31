# V98 NY — seven-slot downside-efficiency and channel-dispersion architecture, preregistration 2026-10-30

**Pre-PnL, new hypothesis.** NY is not a threshold/sign rescue of rejected NV/NW/NX. Its core ranks **downside-adjusted medium-horizon growth** rather than raw momentum, its opportunity follows **range expansion**, RV uses **channel-location dispersion**, and stress trades **realized downside/upside asymmetry**. Goal is maximum compounded growth subject to execution survival, not minimum volatility.

**Data and independence:** pinned Clean-4 BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT Binance USD-M 1h, 2022-12 warmup, 2023-24 training. 2025 already exposed and NOT independent validation; 2026+ holdout untouched; XRP quarantined. Native event rates with signed worst-side official mark-price OHLC envelope (NOT exact funding-tick mark). Never inspect V14/V15/V99 internals for selection.

**Fixed 14-day calendar:** t=744+336k, 53 decisions, signal through close[t], execution at next open t+1. No intra-period target update except risk governor.

1. **Growth Core:** compute 504h and 168h log returns, downside volatility from 504 hourly log returns (RMS of negative part, floor 0.001). Eligibility requires both returns positive; rank by 504h log return divided by downside RMS. Long best +0.72 and second +0.08; if none eligible and >=3 assets negative over 168h, short BTC -0.58; otherwise cash.
2. **Opportunity:** 24h return >0.03, 72h return >0.05, mean (high-low)/close last 24h >1.15 times preceding 168h; long best 24h-return/range-expansion ratio +0.18. This is expansion continuation, not NW's compression breakout or NV's volume migration.
3. **Relative Value:** for ETH, BNB and SOL, 168h channel position (close-low168)/(high168-low168) using all completed OHLC. If max-min >0.40, long lowest percentile +0.12, short highest percentile -0.12. This is channel-location mean reversion, not beta residual or funding spread.
4. **Stress/Recovery:** BTC downside RMS / upside RMS over 168h >1.50, BTC 168h return <-0.04; if BTC 24h return >0.01 long +0.18 (recovery), if BTC 24h return <-0.04 short -0.18 (stress continuation), else cash.
5. **Regime Router:** risk-on if BTC 336h return positive and >=3 assets positive over 168h; risk-on optional multipliers [1,0.7,0.5], risk-off [0.75,1,1].
6. **Dynamic Allocator:** existing causal 336h/21 native funding observation net-log-growth competition, 27 actions (0/0.5/1 per sleeve), 168h forecast horizon, virtual gross <=0.84; all decisions fixed before NY PnL.
7. **Risk Governor:** pretrade all-hour causal projection, atomic one-way net fills, signed 8h funding both settlement orders, all-hour inventory gap checks, intrabar survival, virtual <=0.84 and physical <=0.90 gross. No hidden leverage.

**Binding economic gates (unchanged):** 30 cells = five ablations x base/severe/supersevere costs x two settlement orders; base CAGR >80%, severe >60%, severe max DD <45%, each severe calendar year positive, turnover <=USD600k per USD10k initial NAV; each optional sleeve marginal full-engine log-growth >0.02 and no year marginal < -0.03 for 2023 or 2024. All physical invariants must pass. Reject permanently on any failure; no post-result rescue. Training pass is provisional, NOT independent validation or live authorization.

**Required audits:** independently recompute all 53 raw decisions, independent 17,543-hour signed settlement, independent fills and tamper test, 30-cell arithmetic/economic audit; record hash-linked receipt. Source-only activity counts must be *decision counts*, not inflated hourly-held counts. No claims of exact native funding until authenticated 9,144 event marks exist.
