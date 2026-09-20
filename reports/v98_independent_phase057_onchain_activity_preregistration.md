# V98 Independent — Phase057 on-chain activity feasibility preregistration

Status: FROZEN DATA-FEASIBILITY PROBE; ZERO ALPHA / ZERO RETURNS.

## Independent source family
Phase057 leaves exchange microstructure, derivatives positioning, funding, basis and options data. It tests public blockchain/network activity through the keyless Coin Metrics Community API. The reserved economic family for a later candidate is network-utilization / on-chain activity, not price momentum, basis convergence, participant positioning, or implied volatility.

## Frozen feasibility scope
Assets: BTC and ETH. Metrics: active addresses (`AdrActCnt`), transaction count (`TxCnt`), and total fees in USD (`FeeTotUSD`). Frequency: 1d. Fixed training-era dates: 2023-01-15, 2023-07-15, 2024-01-15, 2024-07-15, 2025-01-15, 2025-07-15. Record only HTTP/data availability, returned timestamp and whether each requested metric is finite/present. Do not calculate changes, ratios, ranks, thresholds, correlations to future returns, alpha, returns or PnL.

## Isolation
Validation is not requested or inspected. Final holdout is not requested or inspected. V99/V16 evidence is excluded. No metric/sign/window/threshold/cadence/asset selection may be inferred from feasibility values.

## Decision rule
If BTC and ETH do not each expose all three frozen metrics in every training year sampled, close Phase057 with no alpha. If they do, mark PASS_DATA_ONLY and authorize exactly one separately preregistered Phase058 on-chain economic mechanism before any PnL. No partial-era/source-substitution rescue.
