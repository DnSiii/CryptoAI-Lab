# V98 Independent — Phase102 perps-volume feasibility preregistration

Status: PRE-REGISTERED before any Phase102 payload inspection, crypto-price join, alpha, PnL, sign, threshold, window search, or parameter selection.

## Purpose
Test whether a genuinely new exogenous market-activity series — aggregate decentralized perpetuals volume — has deterministic daily historical coverage for the frozen V98 training window. This is DATA ONLY. Phase101 protocol-fees is REJECT_NO_RESCUE and cannot be modified or rescued.

## Frozen source and schema
Source: DefiLlama public API. Exact endpoint: `https://api.llama.fi/overview/derivatives?excludeTotalDataChartBreakdown=true&excludeTotalDataChart=false`. Frozen field: top-level `totalDataChart`. Window: 2023-01-01 through 2025-12-31 UTC inclusive (1,096 calendar days). No alternate endpoint/source/category/subset may be substituted after observing the result.

## Gate
`PASS_DATA_ONLY` requires: HTTP success; parseable JSON; daily observations in the frozen field; >=95% calendar coverage; first in-window day <=2023-01-07; last >=2025-12-24; finite non-negative values; zero duplicate normalized UTC dates; strict chronological order after deterministic normalization; raw payload SHA-256 recorded. Any failure => `FAIL_DATA_NO_ALPHA` and Phase102 closes without rescue.

## Isolation
Forbidden in Phase102: crypto prices/returns, funding, V99, V16, Phase083 selection evidence, validation, final holdout, 2026 data, correlations, alpha/PnL, sign/window/threshold/cadence/gross selection. A pass authorizes only a separately preregistered Phase103 hypothesis; it does not authorize same-run economic evaluation.

Rationale: decentralized perpetuals trading volume measures derivatives risk-taking/leveraged activity and is distinct from the already closed spot DEX-volume, TVL, stablecoin-liquidity, sentiment, protocol-fees, Binance positioning/OI and price-derived families.
