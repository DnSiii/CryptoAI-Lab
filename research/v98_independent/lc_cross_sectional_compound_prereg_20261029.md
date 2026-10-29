# V98 Independent LC — preregistration 2026-10-29

**Status: PRE-REGISTERED, NOT VALIDATED.** This is a new complete seven-slot architecture. It is not a repair, sign flip, parameter adjustment, or repackaging of rejected LA/LB/KX/KZ. Rejected candidates remain permanently rejected. Never inspect 2025 validation, 2026+ holdout, old Phase083, XRP, V14/V15/V99 internals, Frozen or paper while selecting LC.

## Economic hypothesis
Persistent cross-sectional **trend leadership** may compound in directional markets; a separate **trend pullback continuation** sleeve may buy temporary dislocations; **cross-sectional momentum dispersion** may harvest relative-value spread; and a **downside-volatility insurance** sleeve may help in stressed regimes. Evaluate marginal wealth contribution to the *complete frozen portfolio*, not standalone profitability.

## Data and execution contract
Authenticated Phase243 Clean-4 BTC/ETH/BNB/SOL USD-M 1h with pinned native signed 8h funding, Dec-2022 warmup, 2023–2024 training only. Decision at completed close t; execute at next actual open t+1. Fixed initial USD10k. Four independently event-frozen unit rows; no hourly re-notionalization, no hidden leverage, no opposing carried inventory, 5% uncommitted reserve, max intended gross 0.95. Gross collateral includes existing and pending positions. Native funding is settled on held signed inventory at actual funding event; native fees/slippage and adverse mark bounds apply.

## Seven slots (fixed before seeing LC historical PnL)
1. **Growth Core, 0.65**: every 672h, rank assets by completed 504h log return, require completed 168h log return positive. Allocate 0.53 to top eligible and 0.12 to second eligible, else idle budget cash. Units persist between scheduled decisions.
2. **Opportunity, 0.12**: every 168h, when idle and median 336h return positive, find assets with 336h return positive, 24h return negative and 6h return positive (a *trend pullback resumption*, not LA acceleration or LB high breakout). Buy the asset with most negative 24h return; hold 168h. Skip immediate reentry on expiry.
3. **Relative Value, 0.10 gross**: every 168h when idle and cross-sectional 168h return dispersion positive, long the strongest 168h relative return (0.05) and short the weakest (0.05), only if strongest 168h return >0 and weakest is lower; hold 168h. This is cross-sectional momentum spread, not LA contrarian residual or LB funding-spread carry. No funding lookahead.
4. **Stress/Recovery, 0.08**: every 168h when idle and median 168h return negative, short the asset with highest realized downside semivolatility over the *prior* 168 completed hourly returns, provided its 168h return is negative; hold 168h. This is downside-volatility insurance, not LB weakest 24h return.
5. **Regime Router**: GROWTH if median 336h return >0; DEFENSE if median 168h return <0; MIXED otherwise. Router restricts Opportunity to GROWTH and Stress to DEFENSE.
6. **Dynamic Allocator**: strict 0.95 gross / 0.05 reserve across persistent event rows, including signed positions, existing inventory and pending exits; ablations leave capital idle.
7. **Risk Governor**: prior-only quote/OHLC/funding bounds; physically settle each hour, stage exits, prohibit same-hour risk-cut refill, reject gross > NAV and inconsistent ledger.

## Immutable source gate before any PnL
18,288 authenticated hourly rows; source manifest hashes and native funding coverage; synthetic and real 14,000-hour future-mutation prefix equality; no invalid quote entries, no silent row rebalance, no component overbudget, gross <=0.95; each optional sleeve >=8 entries in both 2023 and 2024. Any failure rejects LC before PnL; no frequency/threshold/window rescue.

## Economic and independent gates, only after source PASS
5 books (core-only/full/minus each sleeve), base/severe/supersevere, two funding orders, two OS = 30 physical cells; independent receipt reconciliation, settlement oracle, cost sensitivity, annual returns, CAGR, drawdown, PF, payoff, win rate, positive days, tails and concentration. Require full base CAGR >50%, severe CAGR >30%, both 2023/2024 severe positive, severe DD<45%, base and severe turnover <=USD600k; each sleeve full-minus-ablation combined net log growth >0.02 in base and severe, with annual contribution >=-0.03. Reject permanently on any gate failure. Freeze candidate before independent 2025 validation, and open external benchmarks only after internal freeze and validation. No live orders.

**Important:** locally reproduced training PnL without original 30-cell physical receipts and independent oracles is diagnostic only, never a promotion or completed validation.
