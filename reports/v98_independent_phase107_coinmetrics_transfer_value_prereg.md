# V98 Independent Phase107 — adjusted transfer-value feasibility

PRE-REGISTERED before full-payload inspection and before any alpha/PnL.

Mode: **DATA_ONLY_NO_ALPHA_NO_PNL**.

Scientific rationale: test historical availability and integrity of on-chain economic value transfer, which is economically distinct from the already rejected active-address breadth (`AdrActCnt`) and transaction-count (`TxCnt`) hypotheses. Coin Metrics documents `TxTfrValAdjUSD` as adjusted transfer value in USD; Phase107 tests only whether BTC and ETH history is reproducibly available in the Community API.

Frozen source: Coin Metrics Community API, asset-metrics endpoint. Frozen assets: BTC and ETH. Frozen metric: `TxTfrValAdjUSD`. Frozen frequency: 1d. Frozen window: 2023-01-01 through 2025-12-31 UTC inclusive (1,096 expected dates per asset). No source substitution, paid-key fallback, alternate transfer metric, threshold, sign, lookback, correlation or price access is permitted after execution.

PASS_DATA_ONLY requires for BOTH assets: HTTP/JSON success; metric present; >=95% date coverage; first date <= 2023-01-07; last date >= 2025-12-24; finite non-negative values; zero duplicate dates; strict chronological order; raw-response SHA-256 recorded. Any failure => FAIL_DATA_NO_ALPHA and closes this exact source/metric path without rescue.

Isolation: no price returns, trading signal, correlation, PnL, cost/funding computation, parameter search, validation, final holdout, Phase083 selection evidence, V16 or V99 evidence may be read or produced.

Only PASS_DATA_ONLY may authorize a separately preregistered Phase108 economic hypothesis.
