# V98 Independent Phase250 — Funding-Efficiency Allocator decision

Status: **REJECT_FUNDING_EFFICIENCY_ALLOCATOR_NO_RESCUE**.

Phase250 produced the strongest reset-era aggregate result so far, but it failed one frozen chronological gate and therefore cannot be promoted.

BASE:
- structural core: +404.21%, CAGR 71.46%, PF 1.1779, max DD -56.39%
- funding-efficiency allocator: +525.34%, CAGR 84.21%, PF 1.2216, max DD -46.66%
- realized funding drag reduced by 0.24818 equity units

SEVERE:
- core +364.23%
- allocator +465.20%

SUPERSEVERE:
- core +301.68%
- allocator +378.45%

Chronological marginal return versus core:
- 2023: -40.97 percentage points
- 2024: +25.90 percentage points
- 2025: +15.54 percentage points

All frozen gates passed except the rule prohibiting any fold underperformance worse than 5 percentage points. The exact always-on 7d / 30-30-20-20 allocator is therefore rejected without rescue.

No change to its 168h funding window, weights, ranking, asset set or rebalance clock is allowed.

Architecture learning retained:
- funding drag is a material exploitable friction inside the structural beta core;
- simple long-only reallocation can simultaneously increase terminal wealth, PF, stress returns and improve drawdown;
- always-on reallocation is too costly in opportunity terms during at least one high-compounding fold.

The next admissible hypothesis may introduce a genuinely new **economic router** deciding whether funding reallocation is worth its transaction cost. Such a router must use a preregistered break-even condition derived from execution costs, not a threshold selected from Phase250 PnL.

Validation/holdout remain locked. V14/V15/V99 were not used.
