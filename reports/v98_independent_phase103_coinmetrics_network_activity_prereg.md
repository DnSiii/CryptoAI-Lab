# V98 Independent Phase103 — Coin Metrics network-activity feasibility

PRE-REGISTERED before payload inspection and before any alpha/PnL.

Mode: DATA_ONLY_NO_ALPHA_NO_PNL.

Scientific rationale: obtain a genuinely exogenous blockchain-usage series from Coin Metrics Community rather than market price, funding, OI, sentiment, TVL, DEX volume, fees, stablecoin liquidity, or decentralized-perpetuals volume. This phase is feasibility only and cannot select direction, window, threshold, basket, regime, gross, or trading rule.

Frozen source: Coin Metrics Community API (`community-api.coinmetrics.io`), asset metrics endpoint. Frozen assets: BTC and ETH. Frozen metric: `AdrActCnt` (active-address count). Frozen frequency: 1d. Frozen window: 2023-01-01 through 2025-12-31 UTC inclusive (1,096 expected dates per asset). No source substitution is permitted after execution.

PASS_DATA_ONLY requires for BOTH BTC and ETH: HTTP/JSON success; metric present; >=95% date coverage; first normalized date <= 2023-01-07; last normalized date >= 2025-12-24; all observations finite and non-negative; zero duplicate normalized dates; strict chronological order after normalization; raw response SHA-256 recorded independently per asset. Any failed requirement => FAIL_DATA_NO_ALPHA and closes this exact source/metric family without rescue or alternate-source shopping.

Isolation contract: no price returns, trading signals, correlations, PnL, costs, funding, parameter search, validation, final holdout, Phase083 selection evidence, V16 evidence, or V99 evidence may be read or produced in Phase103.

Only PASS_DATA_ONLY may authorize a separately preregistered later economic hypothesis. A pass does NOT authorize same-run alpha/PnL.
