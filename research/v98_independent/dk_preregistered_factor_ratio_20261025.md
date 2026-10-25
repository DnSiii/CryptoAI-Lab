# V98 Independent DK — ex-ante factor compounding with ratio reversion (2026-10-25)

**Ex-ante new complete-engine hypothesis, before source activity or system PnL.** DJ, DI and earlier candidates are permanently rejected. DK does not reuse their signals, parameters, position states or rejected sleeves. It tests *persistent factor leadership plus cointegrated-ratio mean reversion*, distinct from DJ's sparse price-channel/volume breakout and DI's funding carry/inventory hysteresis. Generic V98 physical execution infrastructure is reused without relaxing any risk constraints.

**Data firewall:** exact pinned authenticated Clean-4 BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT Binance USD-M hourly OHLCV and native signed 8h funding/mark bounds, 2022-12 warmup and 2023/2024 chronological training. No 2025 holdout, 2026+, XRP, Phase083, external V14/V15/V99, Frozen, paper or live. At close t, only information <=t; execute at next open t+1.

## Seven preregistered slots
Observation at completed closes every **168 hours** after 1440h warmup. At each observation reprice all module target units using close t and NAV t, then retain until next observation (unless the unchanged conservative governor authorizes risk exits). Tie breaks by fixed asset index.

1. **Growth Core:** for each asset, 336h log return divided by prior 336h hourly return standard deviation times sqrt(336); select up to two with positive 336h log return, highest risk-adjusted momentum; long equal-dollar. Cash if none. This is continuous investable factor leadership, no channel-break trigger or funding rank.
2. **Opportunity Sleeve:** long the single asset with highest 48h log-return acceleration, defined (t-48→t) minus (t-96→t-48), only if acceleration >0.015 and its 336h log return positive. Else flat. No volume breakout or carry threshold.
3. **Relative Value Sleeve:** BTC/ETH log-price ratio mean reversion: z-score of current log BTC/ETH against prior 336 completed ratios [t-336,t-1]; if z>+1.2, short BTC 0.5 gross and long ETH 0.5; if z<-1.2, reverse; else flat. Fixed BTC/ETH pair, no market-mean residual, funding-rank or sign rescue.
4. **Stress/Recovery Sleeve:** compute each asset's close drawdown from its previous 168h maximum; if median drawdown<-0.08 and median 24h return negative, short BTC/SOL equal-dollar; if median drawdown<-0.08 and median 24h return positive, long BTC/SOL equal-dollar; otherwise flat. Uses peak-to-current shock, not DJ's breadth-conditioned 48h shock or DI slow sign transitions.
5. **Regime Router:** RISK_ON when BTC 336h return>0 and >=3 assets 168h return>0; RISK_OFF when BTC 336h return<0 and >=3 assets 168h return<0; otherwise MIXED.
6. **Dynamic Allocator:** [Core,Opportunity,RV,Stress] gross budgets RISK_ON=[3.6,.35,.25,.15], MIXED=[2.4,.45,.45,.35], RISK_OFF=[.8,.25,.5,.55]. One shared physical cash/NAV; no hidden leverage or module-specific collateral.
7. **Risk Governor:** unchanged CG buffered physical authorizer, 336h prior OHLC/672h native funding bounds, 81-corner settlement, 24h staged exit, 0.25% participation, signed native funding and both funding event orderings.

## Immutable acceptance protocol
Source-only first: future-perturbation causal invariance, authenticated manifest, annual active observation epochs >=4 Core, >=4 Opportunity, >=8 RV, >=4 Stress. Reject before PnL if inactive. If passes, run five portfolio paths (core-only/full/minus Opportunity/minus RV/minus Stress) x $10k x base/severe x two funding orderings = 20 physical cells, on Ubuntu 22.04 and 24.04; independently audit cross-OS, basic accounting, annual log growth and marginal full-minus-ablation growth.

All cells must survive; full 2023 and 2024 annual net log growth >0 in both costs/orders; two-year full CAGR >50% base and >30% severe; severe max drawdown <45%; **all three** sleeves strictly positive annual marginal net log growth in both years/costs/orders. No retrospective sign/window/budget/gross changes or cherry-picking. A training pass freezes the complete candidate before supersevere/capacity/independent event-level replay, separate validation, future holdout and external benchmark. A failure freezes DK as rejected. Never authorize live trading.

Only `research/v98_independent/dk_*` and `.github/workflows/v98-independent-dk-*` may be written on `research/v98-independent-zero`.
