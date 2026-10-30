# V98 Independent — Phase058 macro-risk feasibility preregistration

Status: FROZEN DATA-FEASIBILITY PROBE; ZERO ALPHA / ZERO RETURNS.

## Independent source family
Phase058 tests exogenous US macro/risk-state data rather than crypto exchange, derivatives, options, or blockchain-network data. Source is FRED public CSV. Reserved later family: macro liquidity / risk appetite.

## Frozen feasibility scope
Series fixed before inspection: VIXCLS (VIX), DGS10 (10-year Treasury yield), DFF (effective federal funds rate). Fixed training-era business dates: 2023-01-17, 2023-07-17, 2024-01-16, 2024-07-15, 2025-01-15, 2025-07-15. Probe only whether each series is retrievable and finite on every frozen date. No transformations, sign choices, windows, thresholds, crypto returns, correlations, alpha or PnL.

## Isolation and decision
Validation/final holdout are not requested or inspected; V99/V16 evidence is excluded. PASS_DATA_ONLY requires all three series finite on all six dates. Failure closes Phase058 without source/series substitution. Pass authorizes exactly one separately preregistered Phase059 macro mechanism before any PnL.
