# V98 Independent Phase105 — Coin Metrics transaction-count feasibility

PRE-REGISTERED before full-payload inspection and before any alpha/PnL.

Mode: **DATA_ONLY_NO_ALPHA_NO_PNL**.

Scientific rationale: test whether transaction throughput (`TxCnt`) is a reproducible historical information set distinct from the rejected Phase104 active-address breadth signal. Phase057 sampled `TxCnt` successfully on a few dates but did not audit continuous history and did not authorize a trading rule.

Frozen source: Coin Metrics Community API (`community-api.coinmetrics.io`), asset-metrics endpoint. Frozen assets: BTC and ETH. Frozen metric: `TxCnt`. Frozen frequency: 1d. Frozen window: 2023-01-01 through 2025-12-31 UTC inclusive (1,096 expected dates per asset). No source substitution, alternate metric, asset subset, threshold, sign, lookback, correlation or price access is permitted after execution.

PASS_DATA_ONLY requires for BOTH BTC and ETH: HTTP/JSON success; metric present; >=95% date coverage; first normalized date <= 2023-01-07; last normalized date >= 2025-12-24; all observations finite and non-negative; zero duplicate normalized dates; strict chronological order; raw-response SHA-256 recorded independently per asset. Any failed requirement => FAIL_DATA_NO_ALPHA and closes this exact source/metric feasibility path without rescue.

Isolation contract: Phase105 must not read or produce price returns, trading positions, correlations, PnL, costs, funding, parameter search, validation, future holdout, Phase083 selection evidence, V16 evidence or V99 evidence.

Only PASS_DATA_ONLY may authorize a separately preregistered Phase106 economic hypothesis. A pass does NOT authorize same-phase alpha/PnL.
