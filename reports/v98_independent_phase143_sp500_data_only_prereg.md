# V98 Independent Phase143 — SP500 cross-asset DATA_ONLY preregistration

Status: **FROZEN BEFORE ANY SP500 OBSERVATION VALUE, RETURN, CORRELATION, CRYPTO PNL, OR ALPHA IS INSPECTED**.

## Scientific rationale
Phase142 rejected the Treasury-curve family without rescue. Phase143 moves to a scientifically distinct cross-asset risk-appetite family: the FRED S&P 500 level series (SP500). This phase is data-quality only; it cannot select direction, lookback, threshold, or economic parameters.

## Frozen source and window
- Primary series: FRED SP500.
- Training-era observation dates only: 2023-01-01 through 2025-12-31.
- No validation or final-holdout data may be requested or inspected.
- Missing/non-numeric observations are missing; no interpolation, backfill, or imputation.
- Dates must be unique and strictly increasing after normalization.
- Values must be finite decimals.

## Frozen DATA_ONLY gate
Acquire the identical source independently twice. Canonicalize each accepted row as ISO date + normalized finite decimal value and compute SHA-256 over the full canonical row stream.

Mandatory PASS conditions:
1. both acquisitions succeed independently;
2. canonical SHA-256 is byte-identical across acquisitions;
3. global coverage versus expected weekday observations is >=95%;
4. each calendar year 2023, 2024, 2025 independently has >=95% weekday coverage;
5. no duplicate normalized dates;
6. normalized dates are strictly increasing;
7. all accepted values are finite;
8. no accepted observation lies outside 2023-2025.

Any failed gate => REJECT_DATA_QUALITY_NO_RESCUE.

## DATA_ONLY firewall
The Phase143 report may contain only provenance, dates/range, counts, missingness/coverage, integrity flags, and hashes. It must not expose SP500 observation values, extrema, changes, returns; crypto prices/returns; correlation, beta, regression, predictive score, PnL, PF, drawdown, win rate, payoff, regimes, tails, concentration; or any economic parameter selected from observed values.

No economic Phase144 hypothesis may be executed unless Phase143 is persisted as PASS_DATA_ONLY. Any Phase144 economic contract must be separately preregistered before inspecting any relationship between SP500 and crypto.

## Isolation
- Phase083 selection use remains forbidden.
- Validation and all final/forward holdouts remain untouched.
- V16 and V99 evidence/state/reports are forbidden.
- Phase142 is REJECT_NO_RESCUE; Phase143 is not a rescue or parameter variation of it.
