# V98 Independent Phase127 — Global Supply Chain Pressure DATA_ONLY preregistration

## Scientific purpose
Test feasibility of a genuinely orthogonal external macro family: global supply-chain pressure, represented by the Federal Reserve Bank of New York Global Supply Chain Pressure Index (GSCPI). This stage is DATA_ONLY. No numeric series values, descriptive statistics, crypto returns, correlations, directions, alpha, or PnL may be inspected.

## Frozen acquisition/integrity contract
- Training-only calendar window: 2023-01-01 through 2025-12-31 inclusive.
- Official/public Federal Reserve family source only; no V99-derived or internal candidate data.
- Expected monthly frequency: require at least 34 in-window observations (allowing limited publication gaps while preventing a materially incomplete history).
- Require >=95% finite coverage among parsed in-window observations.
- Require strictly increasing dates, zero duplicate dates, zero malformed dates.
- Persist only metadata/counts, HTTP/source status and deterministic payload/date-manifest hashes; never persist numeric observations in the report.
- No fill, interpolation, alternate proxy, endpoint rescue, parameter search, or post-failure parser/source substitution.

## Isolation
Validation and final holdout remain untouched. V16 Frozen, V99 Frozen/research/workflows/reports/paper state are forbidden. Phase083 selection information is forbidden.

## Decision
All frozen integrity gates PASS => PASS_DATA_ONLY, permitting a separately preregistered economic hypothesis in a later phase before any alpha/PnL inspection. Any gate failure => FAIL_DATA_NO_ALPHA and close this family without rescue.
