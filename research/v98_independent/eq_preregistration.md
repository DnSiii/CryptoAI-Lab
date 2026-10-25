# V98 Independent EQ — preregistered positive-carry growth sleeves (2026-10-25)

**Immutable pre-result architecture hypothesis.** EQ tests whether three **long-only, independently activated sources of positive expected return**, rather than short-hedge/factor spreads or reducing turnover alone, can add robust annual geometric wealth to a momentum Growth Core. It is not EP, EO, EN, or other rejected hypothesis tuning/rescue. No prior strategy results are used to choose signs, lookbacks, thresholds or gross. Shared V98 official source, native physical settlement and risk-governor infrastructure only.

## Source firewall
Pinned Clean-4 BTCUSDT ETHUSDT BNBUSDT SOLUSDT Binance USD-M 1h; Dec-2022 744h warmup, 2023/24 chronological training; native funding. No 2025, 2026+, XRP, contaminated Phase083, V14/V15/V99, Frozen, paper or live execution.

## Seven-slot complete portfolio
Signals at completed close t; positions first executable at actual next open t+1. Synchronized 120h inventory epochs. No lookahead, no retroactive backfill, no intraperiod voluntary resizing.
1. **Growth Core:** long-only 336h funding-adjusted positive momentum with positive 72h confirmation, 336h downside-semivol normalized, 20% uniform floor, 80% positive rank weight. Equal fallback.
2. **Opportunity:** long-only alt with strongest 48h funding-adjusted momentum when positive and its 48h quote volume exceeds median of previous 240 completed 48h quote volumes. Flat otherwise. This is directional growth, not a long-short factor.
3. **Relative Value:** long-only cheapest-funding asset over prior 240h when its funding cost is below cross-sectional median by >=0.0003 and its 120h net momentum positive; flat otherwise. Capital seeks relatively better carry *and* positive trend, not a paired hedge.
4. **Stress/Recovery:** long-only strongest 24h recovering asset when prior 120h equal-market return is negative, latest 24h equal-market return positive, and >=2 assets rose in last 24h; flat otherwise. This explicitly targets rebound growth, not a defensive short.
5. **Regime Router:** TREND if 3+ positive 336h net momentum, STRESS if <=1, else MIXED.
6. **Dynamic Allocator:** core 2.6 TREND, 2.2 MIXED, 1.6 STRESS. Active sleeves Opportunity .11, RV .11, Stress .13, core-first and total gross demand <=3.0. All modules long-only; shared collateral; no artificial hidden borrowing.
7. **Risk Governor:** unchanged CG 60% stressed NAV reserve, 81-corner staged-exit viability, native fees/slippage/funding and both funding orderings; no new risk overrides.

## Falsification and release gates
Causal future-mutation test, >=4 active epochs for **each sleeve each training year** before any PnL. If passed: five physical books (core/full/three leave-one-out) x three costs x two funding orders = 30 USD10k 2023/24 cells, cross-OS independent reproduction and artifact reconciliation, independent all-hour ledger if economically viable. Strictly positive 2023 and 2024 full log growth under base/severe both funding orders, and strictly positive **annual marginal full-minus-each-sleeve** log growth under base/severe both orders. Full CAGR >50% base and >30% severe, severe DD <45%, turnover <=USD600k, no hidden leverage, 30/30 survive. Report funding, PF, payoff, win rate, positive days, concentration, tails, costs. No post-result rescue of sign, window, weight, threshold or gross. Training pass and freeze before sealed 2025 validation; external benchmarks only after independent validation.
