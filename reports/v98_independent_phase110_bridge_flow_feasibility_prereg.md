# V98 Independent Phase110 — cross-chain bridge-flow feasibility

PRE-REGISTERED before full payload inspection and before any alpha/PnL.

Mode: **DATA_ONLY_NO_ALPHA_NO_PNL**.

Scientific rationale: cross-chain capital movement is a distinct information family from price, exchange microstructure, funding, on-chain address/transaction counts, native fees, DeFi TVL, DEX volume and protocol fees. Before defining any trading direction, test whether historical chain-level deposits and withdrawals are public, continuous and reproducible.

Frozen source: `https://bridges.llama.fi/bridgevolume/{chain}`.
Frozen chains: `Ethereum` and `BSC`.
Frozen fields: `date`, `depositUSD`, `withdrawUSD`, plus transaction-count fields if returned (not required for pass).
Frozen audit window: 2023-01-01 through 2025-12-31 UTC inclusive.
No alternative host, Pro API, chain substitution, bridge-ID filter, source shopping, direction, threshold, lookback, correlation or price access may be introduced after execution.

PASS_DATA_ONLY requires for BOTH chains: HTTP/JSON success; response is a list of daily records; >=95% coverage of the 1,096 calendar days after filtering the frozen window; first observed date <= 2023-01-07 and last observed date >= 2025-12-24; `depositUSD` and `withdrawUSD` finite and non-negative; zero duplicate normalized dates; canonical date ordering reproducible; raw response SHA-256 recorded.

Any failed requirement => **FAIL_DATA_NO_ALPHA** and closes this exact public bridge-volume path without rescue.

Isolation: no crypto price/return, bridge-flow score, correlation, alpha, PnL, cost/funding, parameter search, validation, future holdout, Phase083 selection evidence, V16 or V99 evidence may be read or produced.

Only PASS_DATA_ONLY may authorize a separately preregistered Phase111 economic hypothesis.
