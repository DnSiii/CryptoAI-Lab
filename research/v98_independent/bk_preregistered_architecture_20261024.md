# V98 Independent BK — native carry-confirmed convex trend + crisis hedge (preregistered 2026-10-24)

**Status:** hypothesis frozen before any BK historical PnL; not a modification or rescue of rejected BH/BI/BJ. Their realized returns are not parameters. Only Clean-4 BTC/ETH/BNB/SOL 1h, Dec2022 warmup and 2023–2024 training. No XRP, 2025/2026+, contaminated Phase083, V14/V15/V99. Do not use 2025 until a complete internally frozen candidate passes all chronological training gates.

Seven slots:
1. **Growth Core:** every 1008 completed hours, fund only assets with positive 168h AND 336h returns, inverse 672h volatility and continuously defined funding-aware discount exp(-4 * positive 168h native funding sum). No named-asset selection. Fixed units until next epoch.
2. **Opportunity:** causal 504h closing breakout >0.5% with positive 72h and >8% 168h trend, funding sum <3%; choose maximum 168h return / 168h vol, fixed 504h exposure, 1008h cooldown.
3. **Relative Value:** 336h signed +.5/-.5 pair, long >2.5% 168h return and short <-2.5%, with >0.5% trailing 168h native funding differential; 672h cooldown. Long funding receiver vs short payer; no hardcoded winner.
4. **Stress/Recovery:** short single highest negative 168h return/vol asset only on >=3 negative 168h and median 72h <-5%, median 24h <-2.5%; close causally on median 24h >2.5%, maximum 168h, 504h cooldown.
5. **Router:** BULL if >=3 positive 168h and median 336h >0; CRISIS if >=3 negative 168h and median 72h <-5%; else NEUTRAL.
6. **Allocator:** core budgets BULL 1.10, NEUTRAL .60, CRISIS .10; opportunity .25/.10/0; relative value .12/.15/.08; stress 0/.10/.35. Events admitted only when their native ex-ante structural trend/carry gate holds, no fitted shadow-PnL or after-result rescue. Fixed-unit sleeve rows, not hourly rebalance.
7. **Risk Governor:** V98-only BA 25% prior exit-capacity, actual t+1 open, 81-corner intrabar settlement, native signed 8h funding, base/severe/supersevere friction, physical liquidation survival.

**Frozen evaluation:** five complete/ablated paths x 3 capitals x 3 fee levels x 2 funding orderings = 90 scenarios on Ubuntu 22.04 and 24.04, 180 receipts audited. Require 90/90 physical survival, zero cross-OS discrepancies, positive full-system 2023 AND 2024 log wealth under base and severe fees for both funding orderings, and strictly positive full-minus-ablation marginal log growth for each of the three complementary sleeves in both years, base and severe, both funding orders. Report supersevere, CAGR, drawdown, PF, payoff, win rate, positive UTC days, turnover, funding, concentration and tails. Rejection is permanent; ablations cannot be promoted. Even a training pass is NOT a separate holdout validation, benchmark superiority, or live trading permission.

**Research reason:** prior source-only native-carry diagnostic documented negative BNB funding and high cross-asset beta, but no asset is hardcoded. New mechanism is a trend-and-carry-aligned factor decomposition, not BJ's trailing shadow profit selector. Optimize long-run compounded wealth subject to survivability, not minimum drawdown.
