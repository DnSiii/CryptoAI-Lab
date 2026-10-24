# V98 Independent AU — preregistered persistent-inventory seven-slot portfolio (2026-10-23)

**Status at registration:** hypothesis only; NO AU historical PnL has been computed. The last fully executed AT architecture is permanently rejected. AU does not reuse AT signals, portfolio allocation or decisions. Reuses only V98 authenticated Clean-4 loader, actual-open signed settlement, causal risk history and the independently tested frozen-unit physical governor.

## Economic thesis and objective
Compounded NET wealth is the objective, not minimum drawdown. Persistent fixed units reduce the implicit hourly notional churn which made AT uneconomic under severe fees. Slow funding-aware leadership, short-lived breakout opportunity, factor-neutral dispersion, and event-only downside protection may contribute independently to the full portfolio. A sleeve need not pass standalone, but must have strictly positive chronological *marginal* net log-growth in BOTH years under base and severe costs.

## Seven slots, fully fixed before first result
1. Growth Core: every 720 completed hours, calculate 336h and 1008h log-return of each Clean-4 asset, subtract the estimated next 90 funding events using the causal mean of the last 126 funding events, and divide by 1008h log-return volatility; only positive net scores and 336h positive return qualify. Allocate 70% to the highest and 30% to second-highest positive score; otherwise leave cash.
2. Opportunity Sleeve: if at least 3 assets have 24h log-return above +3% and quote-volume ratio (current versus prior 336h median) exceeds 1.4, enter the top 24h performer for exactly 96h; 168h cooldown. No future data or revised exit window.
3. Relative-Value Sleeve: every 720h, select the strongest and weakest 336h *risk-adjusted* returns among eligible assets; long strong 0.5 and short weak -0.5 only when the 336h dispersion exceeds 0.08 and their signed expected funding drag is below 0.015 over 90 events. Otherwise flat.
4. Stress/Recovery Sleeve: short the highest 336h volatility asset for at most 72h if >=3 assets have 72h log-return < -0.10 and BTC has 336h negative return; cooldown 336h. No hindsight regime reversal.
5. Regime Router: expansion if BTC 336h log-return >0 and >=3 assets have positive 336h returns; contraction if BTC negative and <=1 asset positive; else transition.
6. Dynamic Allocator: monthly plus opportunity/stress transition only. Base sleeve budgets [0.95,0.25,0.20,0.25], regime multipliers expansion [1,1.2,0.8,0.5], contraction [0.5,0.5,1.2,1.3], transition [0.8,0.8,1,1]. Causal 720h shadow net log-return multiplies each sleeve by clip(exp(2 * trailing net log wealth),0.5,1.5), without future returns. Explicit gross exposure can exceed 1, but no hidden borrowing: physical risk governor may reject or trim.
7. Risk Governor: V98 `v98_persistent_inventory_governor.govern_units` with frozen units set at completed t close and first eligible fill at t+1 actual open. Enforce prior-hour participation, worst rolling 24h exit quote, conservative 24h adverse continuation/funding, 81-corner intrabar actual settlement, no fictitious fills. An unchanged target is NEVER repriced into fresh units.

## Fixed evidence and gates
- Inputs: pinned BTC/ETH/BNB/SOL Binance USD-M 1h, Dec2022 warmup, Jan2023–Dec2024 TRAINING ONLY, native 9,144 funding events, 18,288 hours. XRP quarantined. 2025 future validation untouched; 2026+ never read.
- 5 paths (core_only/full/minus opportunity/minus RV/minus stress) x 3 capital scales (USD10k, 1m, 10m) x 3 fees (base, severe, supersevere) x 2 funding execution orderings = **90 historical cells**.
- Execute in Ubuntu 22.04 and 24.04; independently reconcile all cells, source hashes, outcomes, PnL, turnover, costs, funding, DD, annual CAGR, PF, payoff, win rate, positive days and tails.
- Mechanical survival: all 90/90 cells and strict causal t-1; no forced fill when impossible.
- Economic: both 2023 and 2024 positive NET log growth for full USD10k under base and severe, both orderings. Each complementary sleeve must add strictly positive marginal NET log wealth in both years, base/severe, both orderings, comparing frozen full versus its frozen ablation. Supersevere and capacity are stress evidence, not silently dropped. Reject permanently if gates fail; no post-result threshold/sign/window rescue.
- Do not read 2025 or any external V14/V15/V99 performance until AU or another internally frozen complete candidate passes its own chronological training and separately passes independent validation. No real trading authorization.

**Reproducibility note:** round floating *decisions* only to 12 decimals to prevent cross-OS insignificant arithmetic noise from changing integer event counts; never round cash/PnL or relax economic gates.
