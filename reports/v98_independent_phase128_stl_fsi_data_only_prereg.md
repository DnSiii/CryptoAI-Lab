# V98 Independent — Phase128 preregistration: St. Louis Fed Financial Stress Index DATA_ONLY

Frozen before any Phase128 numeric values, returns, correlations, alpha, or PnL are inspected.

## Scientific question
Can the **St. Louis Fed Financial Stress Index (STLFSI4)** be acquired reproducibly over the V98 training era with sufficient native weekly coverage to justify a later, separately preregistered financial-stress hypothesis?

This is a distinct family from Phase126 NFCI and Phase123 HY OAS: STLFSI4 is a St. Louis Fed composite financial-stress index rather than the Chicago Fed financial-conditions index or a single credit-spread series. This phase tests data feasibility only and makes no directional claim.

## Frozen source and window
- Series: `STLFSI4` only.
- Source: FRED CSV graph endpoint for `STLFSI4` only; no alternate source or series substitution after execution.
- Native cadence: weekly, ending Friday.
- Training-only window: 2023-01-01 through 2025-12-31 inclusive.
- Validation and final holdout: forbidden.

## Frozen DATA_ONLY gates
All must pass:
1. HTTP status 200.
2. Required date/value columns resolve from the frozen STLFSI4 CSV schema.
3. At least 150 in-window weekly rows.
4. Finite coverage >=95% of admitted in-window rows.
5. Zero duplicate dates.
6. Zero malformed dates.
7. Strictly increasing admitted dates.
8. Deterministic SHA-256 payload hash and admitted-date-manifest hash are recorded.

## Anti-overfit / isolation contract
- `numeric_values_exposed = false`: the report may record only structural counts, booleans, status, hashes and date-integrity metadata; no STLFSI4 numeric values/distribution statistics.
- `alpha_or_pnl_inspected = false`.
- No returns, correlations, sign tests, threshold tests, regime tests, parameter search, basket selection or PnL.
- No interpolation, fill, alternate frequency, alternate FRED series, parser shopping, source rescue, partial-era rescue, threshold relaxation, or second-chance endpoint if a frozen gate fails.
- V16/V99/Phase083 evidence is excluded from selection and tuning.

## Decision rule
- All gates pass => `PASS_DATA_ONLY`, authorizing only a separately preregistered Phase129 economic hypothesis before any PnL.
- Any gate fails => `FAIL_DATA_NO_ALPHA`; this exact STLFSI4 source/schema family closes without rescue.
