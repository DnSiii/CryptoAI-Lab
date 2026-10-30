# V98 Independent LA — preregistration, before code and historical PnL (2026-10-29)

**Status: FROZEN DESIGN BEFORE SOURCE IMPLEMENTATION.** LA is an independently hypothesized seven-slot portfolio, not a reweighting or threshold rescue of rejected KX/KZ or other rejected architectures. No benchmark internals, no 2025/2026+, no XRP, no contaminated holdout.

## Economic hypothesis
A multi-asset **close-to-range breakout** core can capture persistent upside convexity without monthly risk-parity exposure to laggards; a short-horizon **positive acceleration** opportunity sleeve captures nascent leadership, while a **contrarian residual** dollar-neutral spread earns reversion rather than momentum, and a **short-drawdown rebound** sleeve enters recovery episodes. Test the complete frozen portfolio; all three sleeves must contribute net positive marginal log wealth. No post-result rescue.

## Source and execution
Phase243 pinned Clean-4 BTCUSDT ETHUSDT BNBUSDT SOLUSDT Binance USD-M 1h, 2022-12 warmup and 2023/2024 TRAINING ONLY. Completed-close t decisions, execute at t+1 actual open. Native signed 8h funding, physical USD10,000, fee/slippage tiers base/severe/supersevere, carried-before-fill and new-after-fill funding order, 2 Ubuntu OS. Source event budget and pretrade capital are not the same as actual collateral; signed cash-aware physical authorization, no unbacked shorts, 5% reserve.

1. **Growth Core, 0.55:** every 672 completed hours, select at most two assets whose 672h and 168h log returns are positive and whose completed close is within 3% of its **prior 672h completed high**. Rank by 672h log return divided by realized 336h hourly volatility; allocate 0.275 to each of top two; if only one eligible, allocate 0.275 and retain the remainder in cash. Hold units between decisions.
2. **Opportunity Sleeve, 0.17:** weekly (168h), if idle, select highest positive **168h minus preceding 168h** log-return acceleration among assets with 168h return positive and 24h return positive. Buy 0.17 for 168h; no signal threshold beyond strictly positive acceleration. No same-close reentry on expiry.
3. **Relative-Value Sleeve, 0.12 gross:** weekly if idle, when median 168h asset log return >0, compute 72h asset log returns minus cross-sectional 72h median; if max-minus-min >0.03, long most negative residual 0.06 and short most positive residual 0.06 for 168h. This is **mean reversion** and opposite KZ's winner-long price dispersion. Signed native funding applies, not a selection input.
4. **Stress/Recovery Sleeve, 0.08:** weekly if idle, when median 168h log return <0 but median 24h log return >0, buy the strongest positive 24h asset for 168h. This is a short-drawdown rebound, not KZ's 336h drawdown criterion.
5. **Regime Router:** TREND if median 168h return >0, RECOVERY if median 168h<0 and median 24h>0, DEFENSE if median 168h<0, else MIXED; gate RV to TREND and Stress to RECOVERY.
6. **Dynamic Allocator:** event-frozen four row positions, total intended gross <=0.92, 5% physical cash reserve, authorize signed physical inventory and prohibit opposite netting or unsettled cash reuse; ablations leave capital idle.
7. **Risk Governor:** prior-only OHLC/liquidity and 672h signed native funding, physically executable margin and staged exit, no liquidation-free leverage assumptions.

## Immutable sequential gates
Source-only authenticated 18,288 hours, pinned manifest and future-mutation causal prefix; zero future leak, no silent rebalance, <=0.92 intended gross, no invalid quote entry, each optional sleeve >=8 independent entries in both 2023 and 2024. Fail = **permanent rejection before PnL**.

Only after source pass: 5 books (core, full, minus each sleeve) x 3 cost tiers x 2 funding orders x 2 OS = 30 physical cells, 60 original receipt audits, five independent every-hour funding settlement oracles, chronological annual metrics, PF, payoff, win rate, positive days, drawdown, tails, concentration, turnover, severe/supersevere. Economic pass requires 2023 and 2024 severe net positive, full base 2y CAGR >50%, severe >30%, severe max DD <45%, base/severe turnover <=USD600k, and each sleeve Full-minus-ablation net log growth >0.02 combined in base/severe with annual contribution >=-0.03. A passing training candidate then freezes internally before **separate 2025 validation**, untouched forward holdout, and only then external benchmarks; no live trading authorization.

No tuning based on the observed 2023/2024 results, no mass grid, no hidden leverage, no holdout peek. A failed hypothesis remains rejected.
