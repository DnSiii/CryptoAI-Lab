# V98 Independent DW — structural beta with shock-convex satellite composition (2026-10-25)

Preregistered before DW source activity or PnL. DV permanently rejected; DW does not retune DV pullback, funding-pair or net-positive-leader signals. Training-only, no 2025+, XRP, contaminated Phase083, V14/V15/V99 signals/parameters/architecture/performance.

**Different economics:** persistent fixed-capital structural market participation, with accelerated continuation opportunity, residual overreaction relative value, and realized-volatility shock convexity. No market-direction sign fitting or conditional core leader selection. Native funding is charged exactly at settlement and evaluated under both ordering conventions.

1. **Growth Core:** fixed long-only 40% BTC, 25% ETH, 15% BNB, 20% SOL; no post-hoc asset selection, always present at the 168h rebalance epoch.
2. **Opportunity:** long one asset with strongest positive 24h log-return acceleration over the previous 24h, requiring 24h return >0, acceleration >0.2%, and recent/prior 24h quote volume ratio >1.0. No DV pullback logic.
3. **Relative Value:** dollar-neutral 50% long the weakest 24h residual to four-asset mean and 50% short strongest, if residual spread >1.0%; independent of native funding rank or long-run price leadership. Funding remains in execution costs.
4. **Stress/Recovery:** when 72h realized volatility relative to 336h exceeds 1.2, 50/50 short BTC/SOL if six-hour equal-weight market return <0, else 50/50 long BTC/SOL if >0. A symmetric convexity sleeve, not a DV 72h price-threshold hedge.
5. **Regime Router:** VOL_SPIKE if realized 72h/336h mean volatility ratio >1.4, else EXPANSION if >=3 assets have positive 168h returns, else BALANCED.
6. **Dynamic Allocator:** (Core,Opportunity,RV,Stress) nominal EXPANSION (3.6,.20,.12,.10), BALANCED (3.1,.18,.16,.18), VOL_SPIKE (1.5,.10,.14,.35); no hidden leverage; all exposure goes through shared physical governor.
7. **Risk Governor:** unchanged CG buffered 60% stressed NAV, 81-corner physical next-open authorization, staged exit, conservative native funding and shared collateral.

Pre-PnL source gate: >=4 Core, >=4 Opportunity, >=8 RV, >=4 Stress active epochs in EACH of 2023 and 2024. On failure reject without PnL. On pass, pinned authenticated 2022-2024 Clean-4 only, 1440h warmup, causal t-close to next actual open, 5 paths x 3 native fee scenarios x 2 funding orders = 30 USD10k physical cells, independently reconciled across Ubuntu 22.04/24.04. Immutable gates: annual net log growth >0 in both years for base/severe both funding orders; each satellite strictly positive annual marginal net log growth for both years base/severe both orders; full 2y CAGR >50% base and >30% severe; severe max DD <45%; turnover <=USD600k; 30/30 survival. PF, payoff, win rate, positive days, tails, concentration, fees, slippage and native funding must be reported. Rejected stays rejected, no post-result rescue.

If training passes, freeze candidate before independent 2025 validation; external V14/V15/V99 comparisons only after separate validation. Never authorize paper/live trades.