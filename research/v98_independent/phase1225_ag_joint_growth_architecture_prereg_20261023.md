# V98 Independent Phase1225 — AG atomic joint-growth portfolio (2026-10-23)

## Independent architectural hypothesis AG-1 (preregistered before AG code/results)
AF Phase1223 is irrevocably rejected (0/180 synthetic cells, carried post-sell concentration); no AF rescue, retuning, imported signal/allocator/governor or modified AF receipt. AG is a **distinct portfolio-level stochastic growth architecture**: forecast and rebalance the entire portfolio in one jointly feasible transaction, rather than AF's sell-then-buy lifecycle. Optimize prospective compounded wealth/net log growth, with survival constraints; no objective to minimize volatility and no promised return ceiling.

Clean-4 only (BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT). Dec-2022 warmup, chronological 2023/2024 training; separate untouched 2025 validation; no 2026+, quarantined XRP, Phase083, or V14/V15/V99 signal/parameter/benchmark reads. Native V98 USD-M funding, actual cash and inventory, no hidden leverage. A synthetic fixture is not authenticated market data.

### Seven fully composed slots
1. **Growth Core:** t-1 close-only long-only 168h drift with 72h downside semideviation, normalized across four assets, continuous and nonnegative. No AF dual EWMA.
2. **Opportunity Sleeve:** t-1 24h close-to-prior-72h-high price breakout **with lagged quote-volume impulse**; zero if no confirmed breakout. No AF synchronized acceleration.
3. **Relative-Value Sleeve:** t-1 cross-sectional 48h excess-return ranking, *long-only* capital rotation funded by actual reductions elsewhere; no short or implicit borrow.
4. **Stress/Recovery Sleeve:** stateful 48h actual-NAV peak/drawdown cash buffer plus fixed 24h hysteresis after recovery; never use intrabar future NAV to place the same order.
5. **Regime Router:** t-1 96h equal-weight breadth and realized market down/up semivariance, independently gates the growth/opportunity/RV mixture.
6. **Dynamic Allocator:** deterministic projected **expected net log-growth** from causal 168h sleeve paper returns after transaction-cost penalty, with precommitted shrinkage and 24h rebalance cadence; this is not a volatility-minimizing objective.
7. **Risk Governor:** jointly solve executable post-trade asset weights and cash in one atomic netted rebalance. Exact signed inventory delta, actual open, explicit fee/slippage, prior 336h quote/minimum depth, prior 336h downside/upside and 720h funding bounds; 81 simultaneous OHLC stress corners; carried exit + future exit reserve; asset concentration and gross limits, no short/borrow, NAV floor. **Never** audit an intermediate post-sell inventory as if it were the final transaction. If the carried portfolio is not jointly feasible at the current open under actual executable limits, reject (do not invent a fill). Optimize feasible growth via deterministic convex portfolio projection, not post-result sign/threshold/cap rescue.

### Precommitted independent gates
A. Unit/invariance tests: source t-1 and future perturbation, seven-slot activity, NAV/cash conservation, joint rebalance order netting, stress-corner constraints, cost/funding, actual exit liquidity.
B. 900h benign and 900h crisis synthetic fixtures, 720h warmup, 180h trading each; crisis 45% all-asset gap at 810 and 80% rebound at 850, rebuilt OHLC, 8h funding. Five ablation paths: core, full, minus opportunity, minus RV, minus stress. Three capital modes $10k/$1m/$10m, three fee regimes, two funding timing orders: **180/180** complete cells; independently rebuild all state per cell. At least one actual stress/recovery activation. No rescue if any cell fails.
C. Two independent OS runners with full receipts and matching numeric/discrete results; then four-OS vendor SHA attestation and freeze, only if B passes.
D. Only after B/C, 90 chronological 2023/2024 authenticated economic training cells, severe/supersevere costs, PF/payoff/win/positive days, max drawdown, tail, concentration, net CAGR, marginal sleeve contribution and reproducibility. Demand robust positive growth in both folds and material improvement over internally frozen V98 baseline, not merely acceptable survival.
E. Only after complete internal training pass/freeze, touch separate 2025 validation; external benchmarks only after that.

A failed complete gate rejects AG, with all receipts preserved. No threshold/window/gross/fee/fixture rescue. No external benchmark access. All AG files strictly V98 Independent namespaced on research/v98-independent-zero.
