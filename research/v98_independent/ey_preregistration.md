# V98 Independent EY — preregistered additive multi-premium growth portfolio (2026-10-26)

**Immutable before EY system PnL.** A genuinely distinct composed architecture from EX: long-only, independent **additive** return-premium sleeves on top of a volatility-balanced buy-and-hold growth core. No self-financed donor rotation, signed carry pair or cross-horizon capital-transfer signal from EX. No rejected architecture's signals, parameters, weights or results are reused; shared authenticated source, settlement, CG governor and audit code are infrastructure.

## Firewall
Binance USD-M Clean-4 BTCUSDT ETHUSDT BNBUSDT SOLUSDT hourly, Dec-2022 warmup, Jan-2023–Dec-2024 training, native event funding and quote-volume physical capacity. Completed t close to t+1 actual open; 2025 untouched, 2026+ never loaded, XRP quarantined, old Phase083 contaminated, V14/V15/V99 benchmarks prohibited before frozen training and separate validation, Frozen/paper/live unchanged.

## Locked seven slots
1. **Growth Core**: every 144 completed hours, allocate 100% of core to four assets by inverse 360h realized volatility, capped per-asset weight at 45% with redistributed remainder (water-filling), no momentum ranking. Core gross demand TREND 2.20, MIXED 1.80, STRESS 1.40.
2. **Opportunity Sleeve**: independent *cross-sectional 72h native-net trend continuation*: if at least two assets have positive 72h native-net return, long the positive leader (highest native-net 72h return) at 0.12 NAV; flat otherwise.
3. **Relative-Value Sleeve**: independent *native funding carry premium*: long the asset with lowest cumulative paid funding in the prior 240h among assets with positive 360h native-net return; require chosen 240h cumulative funding < cross-sectional median; additive 0.12 NAV, flat otherwise.
4. **Stress/Recovery Sleeve**: independent *post-drawdown recovery convexity*: if equal-weight 72h native-net basket return is negative but equal-weight latest 24h native-net basket return positive, long the asset with strongest positive latest 24h native-net return, 0.12 NAV; flat otherwise.
5. **Regime Router**: TREND if >=3 assets have positive 360h native-net return, STRESS if <=1, else MIXED.
6. **Dynamic Allocator**: fixed additive gross sleeves with no funding from core or outcome feedback, 144h synchronized rebalance, max theoretical gross 2.56 under 2.80. No hidden leverage.
7. **Risk Governor**: existing CG 60% stressed-NAV 81-corner buffered physical governor with prior-only native funding, staged 24h exit, quote liquidity, severe/supersevere costs, both funding orderings, unchanged.

## Precommitted gates
Source-only t-1 future mutation invariance and >=4 active epochs per sleeve in each of 2023 and 2024, before system PnL. Five books core/full/three leave-one-out x base/severe/supersevere x both funding orders = 30 native physical USD10k cells; two-OS reproduction, independent artifact-only audit and all-hour independent ledger oracle. Require 30/30 survival, annual positive 2023 and 2024 full log growth base/severe both funding orders, strictly positive full-minus-each-sleeve annual net log growth in each year under base/severe both orders, base CAGR >50%, severe >30%, severe max drawdown <45%, base/severe turnover <=USD600k. Report profit factor, payoff, win rate, positive days, tails, concentration, fees, slippage, funding and gross. No post-result sign, window, threshold, sizing or gross rescue. Failed EY permanently rejected. Separate untouched 2025 validation only after training freeze, then external benchmarks.
