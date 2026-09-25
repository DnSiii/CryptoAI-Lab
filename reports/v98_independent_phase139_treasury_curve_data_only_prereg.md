# V98 Independent Phase139 — Treasury Curve T10Y2Y DATA_ONLY preregistration

Status: PREREGISTERED / DATA_ONLY. No economic hypothesis may be evaluated in this phase.

## Scope and isolation
- Branch: `research/v98-independent-zero` only.
- Training calendar only: 2023-01-01 through 2025-12-31, preserving chronological folds 2023 / 2024 / 2025.
- Validation and final holdout are forbidden inputs and must remain unopened.
- No V16 Frozen, V99 Frozen, V99 research workflow/report/paper/state may be read for tuning or modified.
- New artifacts must remain V98 Independent namespaced.

## Orthogonal data family
Candidate source family: U.S. Treasury 10Y minus 2Y curve (FRED series T10Y2Y). This is a macro term-structure family, scientifically distinct from Phase137/138 real-yield level.

## DATA_ONLY firewall
This phase may acquire and mechanically audit the source, but its persisted report MUST NOT reveal or use:
- observed T10Y2Y values, signs, quantiles, changes or directional summaries;
- crypto returns, future returns, correlations, alpha, PnL, trade outcomes or parameter selection;
- any validation/holdout observation.

## Frozen integrity gates
PASS only if all are satisfied:
1. source identity is exactly T10Y2Y and dates are parseable, unique and monotonically increasing;
2. training-calendar source coverage >= 95% of expected published business-day observations, reported only as counts/coverage percentage;
3. no interpolation/backfill/forward-fill across missing observations;
4. no duplicate dates and no observations dated after the execution date;
5. deterministic normalized representation: two independent executions produce identical SHA-256 and identical aggregate integrity metadata;
6. year-level coverage gates pass independently for 2023, 2024 and 2025;
7. output contains no forbidden economic/value fields and does not access V98 validation/final-holdout configs or artifacts.

FAIL closes this data family at Phase139 with no rescue or threshold relaxation.

## Causality / revision caveat
FRED historical observations can be revised. Phase139 therefore establishes source feasibility and deterministic retrieval only; it does not establish point-in-time vintage correctness. Any later economic Phase140 must explicitly define a causal availability lag and either use an acceptable vintage/PIT mechanism or conservatively justify why revision risk cannot create look-ahead.

## Next-step contract
Only a clean Phase139 PASS permits a separate, persisted Phase140 economic preregistration. Phase140 parameters/gates must be frozen before any T10Y2Y values or crypto performance are inspected. A Phase139 FAIL ends this family.
