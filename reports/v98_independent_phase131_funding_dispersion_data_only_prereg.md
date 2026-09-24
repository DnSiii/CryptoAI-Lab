# V98 Independent — Phase131 Cross-Asset Funding Dispersion DATA_ONLY preregistration

Status: PREREGISTERED AFTER Phase130 REJECT_NO_RESCUE AND BEFORE ANY FUNDING VALUE/DISTRIBUTION/RETURN/CORRELATION/ALPHA/PNL INSPECTION.

## Purpose
Test only whether the existing V98 training-only canonical funding files support a deterministic, causal cross-asset funding-dispersion feature family. This phase is data/integrity only and cannot promote a trading rule.

## Frozen inputs
Only BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT canonical funding files produced by config/v98_independent_phase050_data.json. Calendar window 2023-01-01 through 2025-12-31 UTC. Validation and final holdout are forbidden.

## Frozen eligibility
At each canonical funding timestamp, an observation is eligible only when at least 4 of 5 assets have a finite contemporaneous funding_rate. DATA_ONLY must not print/store funding-rate values, dispersion values, signs, ranks, correlations, returns, or PnL. It may expose only counts, coverage, timestamp boundaries, integrity booleans and SHA256 manifests.

## Gates
- all five canonical funding files exist and expose timestamp/funding_rate;
- >= 3,000 eligible timestamps in 2023-2025;
- eligible timestamp coverage >= 90% of the union of in-window funding-event timestamps;
- zero duplicate timestamps per asset after parsing;
- timestamps strictly increasing per asset;
- zero malformed timestamps;
- zero rows after 2025-12-31 23:59:59 UTC;
- deterministic eligible-timestamp manifest hash.

PASS_DATA_ONLY permits a separate Phase132 hypothesis preregistration before any funding values/distributions or crypto-return join is inspected. Any failure => FAIL_DATA_NO_ALPHA and close this family without parser/threshold rescue motivated by results.

## Isolation
No V16/V99 use; no Phase083 selection use; no parameter search; no rescue; validation/final holdout remain null and untouched.
