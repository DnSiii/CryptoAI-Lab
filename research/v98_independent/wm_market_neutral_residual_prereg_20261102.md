# V98 Independent WM — preregistered residual-beta composed engine (2026-11-02)

**Immutable before any WM Clean-4 PnL.** WM is a new architectural hypothesis based on rolling *beta-hedged residual mispricing* rather than WL's absolute-price ranking, opportunity breakout or simple 72h return spread. WL and all rejected architectures remain rejected; no recovery/tuning. No V14/V15/V99 access.

## Source and causality
Clean-4 BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, Binance USD-M hourly, Dec-2022 warmup, exposed 2023-2025 training only; 27,048 hours and 13,524 signed native funding-rate events. 2025 is **not validation**. 2026+, XRP, Phase083, future holdout, Frozen, V99 and paper are excluded. At completed UTC 23:00 close t, signals use only prices through t and funding observed by t; orders execute no earlier than t+1 open. Daily rebalance; hourly mark-to-market and funding buffer governor.

## Fixed seven-slot system, no grid
1. **Growth Core**: estimate each altcoin's 504-hour BTC beta from hourly log returns using past-only covariance / BTC variance; clip estimated beta to [0,3] to avoid unstable hedge; compute residual return over last 168h (altcoin 168h return minus beta times BTC 168h return). Select strongest positive residual among ETH/BNB/SOL; long +0.28 alt, short BTC -0.28*beta (BTC hedge can be truncated only by portfolio gross cap). If none positive, core inactive. BTC may not be selected by residual.
2. **Opportunity**: for each altcoin, compare last 24h residual return to previous 7 non-overlapping 24h residuals using the same past-only beta; when last residual > +0.03 and greater than all seven prior residuals, long +0.12 selected alt and short BTC -0.12*beta. Select largest residual, ties by asset order. Else inactive.
3. **Relative Value**: compare altcoin 168h residual against its own 504h rolling daily 24h residual distribution, using 21 completed nonoverlapping days; compute z-score (center median, scale MAD*1.4826, floor 0.01). If |z|>1.5, take -0.10*sign(z) alt and opposite BTC beta hedge; choose largest |z|. Else inactive.
4. **Stress/Recovery**: if BTC 168h log return < -0.08 and BTC 24h return > +0.01, long BTC +0.14; if BTC 168h return > +0.08 and BTC 24h return < -0.02, short BTC -0.10; otherwise inactive.
5. **Regime Router**: if BTC 168h return <0, scale Growth Core and Opportunity by 0.60, Relative Value 1.00, Stress 1.00. Else all scale 1.
6. **Dynamic Allocator**: combine sleeves and uniformly scale all slots to <=0.70 gross, preserving hedge ratios, no hidden leverage. No parameter optimization.
7. **Risk Governor**: same independently tested WL hourly physical accounting and funding erosion rule (pre-fill/post-fill ordering; gross/cash >0.75 or cash reserve <22% triggers proportional trim to 0.65 at next open; adverse intrahour margin fails, not rescued). Existing WL rejection remains unchanged.

## Precommitted gates
5 books (full, core-only, minus-opportunity, minus-RV, minus-stress) x 3 illustrative costs (10/20/35bps one-way) x 2 funding/fill orders = 30 physical cells; must survive all. Full base CAGR >80%, severe >60%, severe DD >-45%, severe each calendar year positive. Each of Opportunity, RV and Stress must have strictly positive marginal full-minus-ablation log growth in base and severe, both funding orders. No post-result threshold/sign/window/gross adjustments. Require nontrivial incidence of each sleeve >=30 daily decisions to establish testability, else reject before PnL. Report CAGR, yearly returns, max DD, funding, costs, tails, PF/payoff/win rate, positive days, concentration, causality, full independent hourly ledger replay and tamper detection. These are growth aspirations, not a return ceiling.

## External evidence and no false approval
Original 13,524 exchange markPrice settlement values, historical account-dated fee schedule, bid/ask/depth/impact for order size, and collateral/liquidation rules remain unverified. The mark envelopes and costs are illustrative. Even a training pass is not chronological independent validation or paper/live authorization. Freeze candidate internally and run separate validation before external benchmarks; never open holdout for selection.
