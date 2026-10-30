# V98 Independent — Phase248/249 architecture audit

Status: TRAINING-EVIDENCE ARCHITECTURE AUDIT. No validation/holdout/external engine evidence used.

## Common failure geometry

Phase248 Stress/Recovery and Phase249 inverse-vol allocation were scientifically distinct, but both produced the same architectural warning:

- both materially improved max drawdown versus the +404.21% structural Clean-4 core;
- both improved 2024 and/or 2025 behavior;
- both sacrificed a very large fraction of 2023 compounding;
- both finished with much lower terminal wealth than the structural core;
- both remained positive under severe/supersevere costs but still underperformed the core.

Phase248:
- BASE +269.33%, max DD -40.09%
- marginal fold return vs core: 2023 -119.60pp, 2024 -15.68pp, 2025 +13.18pp

Phase249:
- BASE +298.19%, max DD -43.46%
- marginal fold return vs core: 2023 -153.96pp, 2024 +15.94pp, 2025 +15.46pp

## Architectural conclusion

V98 must not solve drawdown merely by suppressing structural beta whenever risk rises.

The growth engine requires **asymmetric architecture**:
- preserve full participation when the structural beta regime is productive;
- add positive-convex sleeves or cost-efficiency improvements that do not dismantle that participation;
- any Risk Governor / Dynamic Allocator must demonstrate positive terminal-wealth contribution, not just lower volatility.

This does not authorize tuning Phase248 or Phase249. Both exact rules remain rejected without rescue.

Phase250 therefore attacks a different friction: realized funding drag while holding gross 1.0 and maintaining all four assets long.
