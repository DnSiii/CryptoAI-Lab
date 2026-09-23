# V98 Independent — Phase123 Credit Stress DATA_ONLY preregistration

Status: PREREGISTERED BEFORE DATA INSPECTION / ZERO ALPHA / ZERO RETURNS / ZERO PNL.

## Scientific family
External US credit-risk stress via FRED ICE BofA US High Yield Index Option-Adjusted Spread (`BAMLH0A0HYM2`). This is economically distinct from V98 crypto microstructure/on-chain/stablecoin families, DXY, Fed balance-sheet WALCL and ON RRP.

## Frozen scope
- Source: FRED public CSV, series `BAMLH0A0HYM2` only.
- Window: 2023-01-01 through 2025-12-31 training only.
- No validation or final-holdout access.
- No V16/V99 inputs, reports, state or selection evidence.
- DATA_ONLY phase: observation values, descriptives, correlations, returns, direction, alpha and PnL MUST NOT be emitted or inspected.

## Canonicalization and gate
Parse ISO `observation_date`; retain only finite series observations inside the frozen training window. Calendar rows whose series value is missing (`.`/blank/nonfinite) are treated as source-calendar missing observations, not malformed records. No fill, interpolation, imputation or date substitution is permitted.

PASS_DATA_ONLY requires all of:
1. HTTP 200 after deterministic bounded retries;
2. >=95% coverage of weekdays in frozen training window using finite observations;
3. zero malformed-date records;
4. zero duplicate finite observation dates;
5. zero finite observations outside training window;
6. deterministic payload and canonical-row SHA256 hashes.

Failure => `REJECT_DATA_SOURCE_NO_RESCUE`. No source substitution or parser tuning after result.

If PASS_DATA_ONLY, any economic Phase124 hypothesis must be separately preregistered before observing series values, descriptives, correlations or any PnL.
