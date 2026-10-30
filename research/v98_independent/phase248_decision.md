# V98 Independent Phase248 — Stress/Recovery Sleeve decision

Status: **REJECT_STRESS_RECOVERY_NO_RESCUE**.

The preregistered volatility-confirmed downside-breadth sleeve improved drawdown and worst-day behavior, but it sacrificed too much compounded wealth relative to the structural Clean-4 core.

Training evidence, BASE:
- structural core: +404.21%, CAGR 71.46%, PF 1.1779, max DD -56.39%
- Phase248 combined: +269.33%, CAGR 54.56%, PF 1.1726, max DD -40.09%

SEVERE fell from core +364.23% to +230.31%.
SUPERSEVERE fell from core +301.68% to +173.78%.

Chronological marginal return versus core:
- 2023: -119.60 percentage points
- 2024: -15.68 percentage points
- 2025: +13.18 percentage points

The sleeve successfully reduced crash exposure, but the exact breadth-3 + RV24-above-30d-q80 half-exposure rule is too defensive for the V98 North Star. Seven frozen gates failed: BASE return, CAGR, PF, fold breadth, fold underperformance, severe return and supersevere return.

No adjustment to the 168h breadth window, 24h realized-vol window, q80 threshold, 720h reference, -0.125 sleeve weight, daily decision clock or sign is permitted as a rescue.

Architecture learning retained:
- stress reduction can materially cut drawdown;
- the V98 system cannot pay for protection by giving up this much compounding;
- future Stress/Recovery candidates should seek positive convex payoff rather than broad de-risking.

Validation/holdout remain locked. V14/V15/V99 were not used.
