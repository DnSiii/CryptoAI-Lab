# V98 Independent — Phase158 STLFSI4 DATA_ONLY transport audit

Date: 2026-09-26
Scope: V98 Independent only

## Evidence reviewed

- Workflow run `36279908712`, first job `108518195278`.
- Failure occurred inside `urllib.request.urlopen` while reading the FRED `fredgraph.csv` endpoint for `STLFSI4`.
- The implementation attempted 4 bounded acquisitions with 45 s timeout and exponential backoff; all exhausted on network read timeout before a canonical dataset or economic statistic was produced.
- The failure therefore does **not** constitute scientific rejection of STLFSI4 and must not be interpreted as economic evidence.

## Integrity / anti-overfit audit

- Series remains fixed: `STLFSI4`.
- Window remains fixed: 2023-01-01 through 2025-12-31.
- This phase remains DATA_ONLY: no crypto returns, PnL, correlation, threshold search, sign search, validation, final holdout, V16 or V99 evidence may enter the gate.
- No imputation/carry-forward is permitted.
- PASS still requires two independent acquisitions to canonicalize to identical SHA-256 plus the frozen coverage/integrity gates.
- A transient source outage is transport evidence only; it cannot relax any data-quality gate.

## Reproducibility decision

The retry of the same frozen workflow is scientifically admissible because it changes no hypothesis, series, date window, transformation, threshold, direction, fold, cost, or acceptance criterion. If a retry succeeds, the resulting canonical hash must still satisfy the pre-existing double-acquisition equality check.

## Next action

Harvest retry job `108526663092`. On `PASS_DATA_ONLY`, freeze the canonical hash before preregistering any economic hypothesis. On another transport failure, continue with a source-availability engineering path that preserves the exact series/window and does not inspect crypto outcomes.