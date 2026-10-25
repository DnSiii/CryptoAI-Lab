# V98 Independent DN — preregistration (2026-10-25, before economic execution)
Status: NEW hypothesis, not an approved engine. Rejected V98 experiments remain rejected and cannot be rescued; no V14/V15/V99 benchmark input, no 2025+ access, no Phase083, XRP quarantined.
## Distinct seven-slot architecture
Growth Core: always-long, four-asset Clean-4 structural perpetual risk-premium basket, initially equal weighted; weekly 70/30 smoothed inverse 336h downside variation plus native funding burden. No asset selection based on realized 2023/2024 profits.
Opportunity: prior-only 24h close-location/quote-flow continuation with positive 168h net-of-native-funding trend.
Relative Value: 168h cross-sectional native funding spread, dollar-neutral short high-funding payer / long low-funding payer, min spread 0.0005.
Stress/Recovery: negative breadth/volatility acceleration short ETH/SOL, or 24h BTC reversal after negative 72h long BTC/SOL.
Regime Router: 168h funding-adjusted breadth and 336h BTC net direction.
Dynamic Allocator: precommitted budgets RISK_ON (3,.25,.18,.18), MIXED (2.2,.20,.22,.25), RISK_OFF (1,.10,.25,.55), with overlap discount. No retrospective PnL-based choice.
Risk Governor: existing V98 CG buffered shared-collateral physical authorization, native signed funding, 81-corner settlement and next actual open execution, unchanged.
## Immutable acceptance
Authenticated Clean-4 Binance USD-M hourly Dec 2022–Dec 2024, 1440h warmup, weekly 168h decisions at completed close t executed at actual next open t+1. Activity min per year 2023 and 2024: core 4, opportunity 4, RV 8, stress 4. Exactly five paths (full/core-only/three leave-one-out) x base/severe/supersevere x both funding orderings = 30 physical cases duplicated on Ubuntu 22.04/24.04, independently reconciled. Physical survival/no hidden borrowing; 2023 and 2024 positive net log growth under base/severe both orderings; each sleeve strictly positive marginal log growth both years under base/severe and both orderings; two-year full CAGR >50% base and >30% severe; severe drawdown <45%; turnover <=USD600k. Supersevere physical survival and tails required. Fail any gate -> REJECT_DN, no post-result threshold/sign rescue. Only a frozen passing candidate can advance to separate chronological validation, unopened future holdout and external benchmarks. No paper/live permission.
