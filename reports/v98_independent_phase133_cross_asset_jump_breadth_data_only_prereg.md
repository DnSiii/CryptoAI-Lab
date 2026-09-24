# V98 Independent — Phase133 Cross-Asset Jump Breadth DATA_ONLY preregistration

Status: PREREGISTERED AFTER Phase132 CLOSED_DUPLICATE_NO_RESCUE AND BEFORE ANY PHASE133 FEATURE VALUE/RETURN/CORRELATION/ALPHA/PNL INSPECTION.

## Purpose
Test only whether the existing V98 training-only hourly canonical price files support a deterministic, causal cross-asset jump-breadth feature family. This is orthogonal to Phase131/071 funding dispersion: it uses only completed hourly close returns and no funding values.

## Frozen inputs
BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT canonical hourly market files produced by config/v98_independent_phase050_data.json. Calendar window 2023-01-01 through 2025-12-31 UTC. Validation and final holdout are forbidden.

## Frozen DATA_ONLY construction eligibility
For each UTC day, require at least 23 finite completed hourly close-to-close returns for each of at least 4 of 5 assets. A day is eligible only when this condition holds. DATA_ONLY may expose counts, coverage, timestamp boundaries, missingness/integrity booleans and deterministic SHA256 manifests only. It must not print/store hourly returns, jump thresholds, jump counts, cross-asset breadth values, correlations, forward returns, ranks, alpha or PnL.

## Gates
- all five canonical hourly price files exist and expose timestamp/close;
- >= 1,000 eligible UTC days in 2023-2025;
- eligible-day coverage >= 95% of calendar days in the frozen window;
- zero duplicate timestamps per asset after parsing;
- timestamps strictly increasing per asset;
- zero malformed timestamps;
- zero rows after 2025-12-31 23:59:59 UTC;
- deterministic eligible-day manifest hash.

PASS_DATA_ONLY permits a separate Phase134 economic hypothesis preregistration before any Phase133 feature values or return joins are inspected. Any failure => FAIL_DATA_NO_ALPHA and close without threshold/parser rescue motivated by outcomes.

## Isolation
V98 Independent only. No V16/V99 use; no Phase083 selection use; no parameter search; no rescue; validation/final holdout remain null and untouched.
