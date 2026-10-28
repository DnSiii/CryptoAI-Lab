# V98 Independent JU — pre-economic hypothesis: passive liquidity absorption (2026-10-28)

**Status: preregistered BEFORE JU implementation, source viability, and economic PnL.** This is a new seven-slot system hypothesis, not a repair of rejected JT, JS, JR, JN, or JP. Rejected architectures remain frozen. No 2025 validation, future holdout, 2026+, V14/V15/V99 internals, V16/V99 Frozen, paper, or live orders.

## Independent economic mechanism and authenticated source
The mechanism is **passive liquidity absorption**: a rising last-half 5m price despite a minority of aggressive buyer volume indicates resting bids absorbing sellers, whereas falling price with aggressive buyers dominating indicates offers absorbing buyers. Unlike JR's *change in taker initiative* and intrahour trough/rebound momentum, JU tests **opposition between aggressive taker direction and achieved price impact**. Unlike JT's contemporaneous cross-asset downside beta, JU is within-asset price/flow mismatch. The new hypothesis is prospective and must fail without rescue if economically unproductive.

Source: exact already dual-OS authenticated native Binance USD-M 5m masked artifact `v98-native-5m-masked-ubuntu-24.04` from run 40668217706, pinned feature CSV SHA256 `423b2394d8478157361c2d7c72238771ffb2ec01fcad6ae53142733e03840e6c`; 100 source ZIPs, 67,296/73,152 valid asset-hours, eight quarantined asset-months. Source columns are last-half aggressive buyer quote share, last-half rebound/selloff, path realized volatility, each computed only from **completed hour t**. Pin official Clean-4 1h Dec-2022..Dec-2024 and native funding via artifact run 40064588623; no 2025 or later read. Any 168h source-mask violation disables all optional sleeves, returns budget to Core.

For asset i and hour t, define `sell_absorb=max(0,.5-late_taker_share)*max(0,late_rebound_log)/max(path_realized_vol,.001)` and `buy_exhaust=max(0,late_taker_share-.5)*max(0,-late_selloff_log)/max(path_realized_vol,.001)`. Fixed 48h means, no fitted sign or threshold, no grid.

## Complete seven-slot portfolio (one immutable hypothesis)
1. **Growth Core**: weekly long top two assets by last 504h native-funding-net momentum / last 168h downside semivol (floor .001), weights 65/35.
2. **Opportunity**: long asset with greatest 48h mean sell absorption if strictly positive; otherwise return capital to Core. Fixed budget 0.16.
3. **Relative Value**: signed 50% long asset with highest sell absorption and 50% short *distinct* asset with highest buy exhaustion (stable rank excluding long); fixed budget 0.12.
4. **Stress/Recovery**: continuous complementary long asset; STRESS chooses minimum last 168h path realized volatility; RECOVERY chooses highest 48h sell absorption; NORMAL chooses highest 168h funding-net positive momentum **excluding the highest Core leader where possible**. Fixed budget 0.14.
5. **Regime Router**: STRESS if 72h equal-weight native-net return < -0.025 or 24h / 168h mean path realized volatility > 1.6; RECOVERY if 24h equal-weight net > .01 and prior 72h net < 0; otherwise NORMAL, stress precedence.
6. **Dynamic Allocator**: every 168h completed-close, allocate Opportunity .16 when active, RV .12, Stress/Recovery .14, remainder Core (>= .58). Independent Full and three Full-minus-sleeve books reallocate removed sleeve budget to Core; Core-only separately financed. No post-result budget, threshold, sign or window changes.
7. **Risk Governor**: existing V98 order-invariant buffered shared collateral; prior-only risk and exit-capacity, actual next-hour open, signed native funding, base/severe/supersevere costs, both funding orderings and independent 81-corner settlement. Regime gross NORMAL .90, STRESS .72, RECOVERY .85. No leverage hidden in sleeve weights.

## Immutable gates and stop conditions
Before PnL: verified exact native 5m source CSV SHA and receipt, 1h pinned official source, causal future-mutation, masked source fallback, gross <=1, all three financed Full-minus-sleeve target L1 > .025 at >=8 weekly epochs in **each** 2023 and 2024. Failure => terminal source-only rejection, no economic run.

After pre-PnL pass: five separately financed books x 3 cost tiers x 2 funding orders x 2 OS = 30 cells; all-hour independent 81-corner settlement oracle; original receipt-only independent audit. Require all 30 physical survivals, 2023 and 2024 positive full native-net log wealth under base/severe, 2023-24 CAGR >50% base and >30% severe, severe drawdown <45%, turnover <=USD600,000 under base/severe. Each optional sleeve Full-minus-ablation must exceed +.02 combined log wealth in both base/severe and each funding order, with annual marginal >=-.03. Report PF, payoff, win rate, positive days, concentration, tail CVaR, signed funding, turnover, drawdown and reproducibility. Rejection is permanent; no rescue after observed PnL.

Training pass **does not authorize** 2025 validation or paper/live. Only then freeze complete JU, run separate chronological 2025 validation, untouched future holdout, and external benchmark after internal freeze.
