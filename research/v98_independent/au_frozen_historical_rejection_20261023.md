# V98 Independent AU — frozen historical rejection (2026-10-23)

**Status: REJECTED, permanently.** This is not a validated trading engine, and no 2025 holdout, 2026+ data, V14/V15/V99 benchmark, V16/V99 frozen state or V99 paper was accessed/modified.

Official two-OS pinned-source 90-cell execution: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40046972207
Evidence artifact: `au90-official-economic-summary` (ID 12542225708).
Preregistered source: `au_persistent_growth_prereg_20261023.md`.

- 90/90 cells **recorded**, 70/90 survived; **20/90 failed physical/economic survival**. Both OS numerically reconciled with **zero differences** in the official strict receipt comparator.
- Full USD10k base, carried-before-fill: 2y CAGR **-77.66424856833423%**, 2023 CAGR **-73.37945810571764%**, 2024 CAGR **-81.25037935794401%**, max drawdown **95.24090370195286%**. Final NAV **USD497.86313099098095** from USD10k. This is a historical training result, not forecast or live PnL.
- Full USD10k base: turnover **USD12,957,053.10**, fees **USD6,478.53**, slippage **USD6,478.53**, native funding **-USD193.08**, **6,420** nontrivial physical fill hours from **152** signal target updates.
- All four preregistered USD10k base/severe annual growth gates failed; Opportunity, RV and Stress marginal gates all failed. Full path only 15/18 survived. Example first faults: supersevere USD10k at t16749 `V98_UNIT_EMERGENCY_COLLATERAL`, USD10m base at t5109 `V98_UNIT_EMERGENCY_EXIT_TOO_SLOW`. These are valid rejection outcomes, not bugs to waive.

## Root-cause / distinct next engineering direction
The frozen-unit physical executor passed isolated no-churn tests, yet in full historical integration its repeated risk-constrained partial fills / risk exits generated thousands of trades and multi-million turnover despite sparse signal updates. Thus *freezing intended units alone is insufficient*: the governor must avoid re-authorizing a trimmed risk position every next hour. Do not alter AU parameters, suppress failures or rerun AU with different signs/windows/thresholds.

A **new independently preregistered complete engine**, with different signal sources and allocator, should incorporate a first-opening **risk authorization that is frozen for an epoch**, monotone no-re-risk after any forced de-risk, and physical liquidity slicing with native funding. Prove the no-churn property at portfolio-history level, not just static tests. Then run the full 90-cell economic matrix before touching 2025. No artificial CAGR promise or live deployment.

**Decision:** no V98 champion approved; AU is NOT eligible for holdout or external benchmarking.
