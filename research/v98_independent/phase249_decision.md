# V98 Independent Phase249 — Dynamic Allocator decision

Status: **REJECT_DYNAMIC_ALLOCATOR_NO_RESCUE**.

The preregistered 30-day inverse-volatility / 40% cap allocator improved drawdown but sacrificed too much compounded wealth relative to the structural Clean-4 core.

BASE:
- structural core: +404.21%, CAGR 71.46%, PF 1.1779, max DD -56.39%
- inverse-vol allocator: +298.19%, CAGR 58.49%, PF 1.1825, max DD -43.46%

SEVERE fell from +364.23% to +265.52%.
SUPERSEVERE fell from +301.68% to +215.80%.

Chronological marginal return versus core:
- 2023: -153.96 percentage points
- 2024: +15.94 percentage points
- 2025: +15.46 percentage points

The allocator materially reduced drawdown and funding drag, but it under-allocated the strongest compounding regime and failed the North Star wealth objective. Five frozen gates failed: aggregate marginal return, CAGR, fold underperformance, severe return and supersevere return.

No change to the 720h volatility window, 40% cap, inverse-vol score, daily rebalance clock, or asset set is permitted as a rescue.

Architecture learning retained:
- pure risk equalization is too defensive for V98;
- funding drag reduction is economically meaningful and deserves a separate, non-price-based allocator hypothesis;
- future allocator research must preserve bull compounding while reducing carrying-cost leakage.

Validation/holdout remain locked. V14/V15/V99 were not used.
