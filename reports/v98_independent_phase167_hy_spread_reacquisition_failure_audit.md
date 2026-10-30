# V98 Independent — Phase167 HY spread reacquisition failure audit

Date: 2026-09-27

## Scope
Independent audit of Phase166 DATA_ONLY evidence only. No economic PnL, no validation/final-holdout access, no V99/V16 dependency.

## Evidence
Phase166 reacquired FRED series BAMLH0A0HYM2 twice with identical SHA-256 `5217b618029007c82de537370a13ba447f54b9e574315d7fbd216bcbf538f0ff`.

Window 2023-01-01..2025-12-31: 594 observations vs 783 expected weekdays; global coverage 75.8621%. Annual coverage: 2023 26.9231%, 2024 100.3817%, 2025 100.0%. QA: duplicate dates 0, malformed dates 0, nonfinite 0, negative 0, out-of-window 0, missing-value rows 7.

## Diagnosis
The rejection is not a transient transport/reproducibility failure: independent acquisitions are byte-identical and the integrity checks pass. The decisive defect is historical coverage concentrated in 2023. Re-running the same source or relaxing the >=95% global / >=90% annual gates would be rescue/threshold weakening and is prohibited.

The >100% 2024 weekday ratio is a denominator-calendar artifact (official observations can include dates outside the simplistic weekday expectation); it does not repair the 2023 deficiency and is not a justification to alter the preregistered gate after seeing evidence.

## Decision
`REJECT_DATA_QUALITY_NO_RESCUE` remains final for the Phase166 HY family in this research line. Do not backfill from Phase151, impute, carry forward, trim the window, or launch an economic HY-spread hypothesis from this dataset.

## Next scientifically distinct step
Move to an orthogonal, independently sourced macro/liquidity family under a fresh DATA_ONLY preregistration. Preserve economic firewall until source integrity, chronology, coverage and deterministic replay pass.
