# V98 Independent EO — preregistered self-financing portfolio factor tilts (2026-10-25)

**PRE-RESULT immutable hypothesis.** EO is a *joint* seven-slot portfolio, not EN online-shadow evidence, EM displaced-wealth gate, EL capital vacancy, or rescue of any rejected strategy. EN/EM results and weights are not used to set EO signs, lookbacks, thresholds, leverage or fees. Only authenticated Clean-4 and generic V98 physical settlement/governor code may be reused.

## Source firewall
BTCUSDT ETHUSDT BNBUSDT SOLUSDT Binance USD-M 1h, 2022-12 744h warmup, 2023/24 training only. Pinned official OHLC and native funding. No XRP, 2025, 2026+, contaminated Phase083, V14/V15/V99, Frozen, V99 research/paper or live trading.

## Seven slots and causal execution
Completed close t determines orders at next actual open t+1. Signals use only <=t. All four sources independently recompute at completed closes every 72h (Stress every 24h), no hidden resizing between observations.

1. **Growth Core:** long-only cross-sectional 480h native-funding-adjusted momentum requiring 120h positive confirmation, with 25% equal-weight floor and 75% positive rank weights; fallback equal.
2. **Opportunity Sleeve:** a *zero-net* factor tilt: at 72h observations, rank 72h positive funding-adjusted momentum and 24h volume surprise. If the strongest has both positive momentum and 24h quote volume above the previous 168 completed 24h-volume median, long strongest 0.5 and short weakest 0.5, only if different. Unlike prior breakout or shadow-gated sleeves, this is capital-neutral breadth rotation.
3. **Relative-Value Sleeve:** a *zero-net* liquidity-quality tilt: rank 240h high-low range efficiency, defined by net 240h price change divided by sum of completed 240h high-low ranges (bounded), among four assets. Long highest positive-efficiency asset 0.5 and short lowest negative-efficiency asset 0.5, only if sign separation exists.
4. **Stress/Recovery Sleeve:** at 24h observations, detect a 72h market drawdown >3% followed by positive 24h equal-market return with 3+ assets rising; long the strongest recovering alt 0.5 and short the weakest recovering asset 0.5. This is a post-crisis recovery factor, not EN short-crash continuation or EM defensive hedge.
5. **Regime Router:** TREND if 480h funding-adjusted breadth >=3, STRESS if <=1, else MIXED.
6. **Dynamic Allocator:** fixed joint gross demand Growth Core TREND 2.0, MIXED 1.8, STRESS 1.4; factor tilts Opportunity .12, RV .12, Stress .16 only when their causal source is active. Gross requested <=2.40, absolute cap 2.40, core-first. **These sleeves are zero-net long-short capital reallocations inside one netted position book, not independently leveraged portfolios.** Their physical incremental growth must be measured by full-minus-leave-one-out, not hypothetical standalone PnL.
7. **Risk Governor:** unchanged CG 60% stressed NAV reserve, 81-corner staged-exit physical viability, prior-only quote/funding, next actual open, native signed funding and base/severe/supersevere both settlement orderings. No unreported leverage.

## Preregistered gates
Synthetic future mutation preserves earlier signal/update/regime/budget. At least 4 active epochs per sleeve in **each** training year. If source passes: five full physical paths (core-only, full, minus each sleeve) x 3 costs x 2 funding orders = 30 USD10k training cells, independent Ubuntu22/24 reproduction, no hidden borrow, complete ledger, and independent artifact reconciliation. All 30 survive; full base and severe annual log growth positive in 2023 and 2024 both funding orders; full-minus-each-sleeve annual log growth >0 in each year under base/severe both orders; full CAGR >50% base and >30% severe; severe max DD <45%; turnover <=USD600k. Include native funding, fees, slippage, turnover, PF, payoff, win rate, positive days, concentration and tails. No sign/threshold/weight rescue if rejected.

Only after training pass and internal freeze may the separate sealed 2025 chronological validation be touched. External benchmarks only after independent validation. No paper/live trading authorization from training results.
