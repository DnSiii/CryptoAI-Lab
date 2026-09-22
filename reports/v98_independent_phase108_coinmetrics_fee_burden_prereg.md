# V98 Independent Phase108 — native fee-burden feasibility

PRE-REGISTERED before full-payload inspection and before any alpha/PnL.

Mode: **DATA_ONLY_NO_ALPHA_NO_PNL**.

Scientific rationale: blockchain fee burden is an economically different observable from address count, transaction count and USD transfer value. To make BTC and ETH comparable without using market prices, the intended future observable would normalize native transaction fees by native current supply. Phase108 only tests whether both required raw metrics are continuously and reproducibly available; it does not compute that ratio for selection and does not inspect any trading outcome.

Frozen source: Coin Metrics Community API asset-metrics endpoint.
Frozen assets: BTC and ETH.
Frozen metrics: `FeeTotNtv` and `SplyCur`.
Frozen frequency: 1d.
Frozen window: 2023-01-01 through 2025-12-31 UTC inclusive, 1,096 expected dates per asset.
No source substitution, paid-key fallback, alternate fee/supply metric, asset subset, threshold, direction, lookback, correlation or price access is permitted after execution.

PASS_DATA_ONLY requires, for each BTC/ETH × metric pair: HTTP/JSON success; metric present; >=95% date coverage; first date <= 2023-01-07; last date >= 2025-12-24; finite non-negative values; zero duplicate dates; strict chronological order; raw-response SHA-256 recorded. All four pairs must pass. Any failure => FAIL_DATA_NO_ALPHA and closes this exact fee-burden data path without rescue.

Isolation contract: no price returns, trading signal, normalized fee-burden score, correlation, PnL, costs, funding, parameter search, validation, final holdout, Phase083 selection evidence, V16 evidence or V99 evidence may be read or produced.

Only PASS_DATA_ONLY may authorize a separately preregistered Phase109 economic hypothesis.
