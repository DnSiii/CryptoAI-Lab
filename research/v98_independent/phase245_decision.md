# V98 Independent Phase245 — Growth Core decision

Status: **REJECT_GROWTH_CORE_NO_RESCUE**.

The frozen broad market-state core returned +106.31% BASE (27.30% CAGR, daily PF 1.1695) with -49.41% max drawdown. Severe remained +85.70% and supersevere +55.52%; 2023 and 2025 were positive, 2024 was -4.12%.

It failed exactly two preregistered gates: max drawdown worse than -45%, and BASE return did not exceed the preregistered Clean-4 passive reference.

The passive Clean-4 reference itself returned +404.21%, CAGR 71.46%, PF 1.1779 and max drawdown -56.39%. This is a diagnostic discovered under a frozen reference rule, not an external-engine benchmark.

Phase245 is rejected without changing 30d/120d horizons, breadth=3, daily clock, sign, or flat-state rule.

Architecture implication: the reset V98 should not automatically discard strong structural crypto beta. The next experiment may treat that preregistered passive reference as a Growth-Core primitive and test a separately preregistered Risk Governor. This does not resurrect Phase245.
