# V99 R106 Phase130 — execution incident (2026-09-24)

## Classification
TECHNICAL / PRE-PNL. This incident is not scientific evidence for or against Phase130.

## Observed failure
GitHub Actions run 35981920291 failed during runner setup before checkout/feature construction/backtest. The runner could not resolve `actions/setup-python@a26af69be951213d495a4c3e4e4022e16d87065`.

## Root cause
The Phase130 workflow contained a one-character-corrupted setup-python pinned SHA. The immediately preceding successful Phase129 workflow used `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065`.

## Correction
Only the workflow action pin was corrected. Phase130's preregistered scientific specification, script, train cutoff, direction, 24h window, gross allocation, cost model, temporal-fold criteria, and downstream gates were not changed. Commit: `dbad7a1e61f0f3d50354f3561783d570c01f9538`.

## Integrity / anti-overfit decision
Because execution stopped before checkout and PnL, no result was observed and no scientific degree of freedom was consumed. Phase130 remains preregistered exactly as written in `research/v99_r106_phase129_rejection_and_phase130_prereg.md`. No sign flip, window change, threshold change, asset deletion, cost change, or holdout access is permitted.

## Required next action
Execute the corrected workflow. Decide Phase130 only from the preregistered severe train-only gate and chronological folds. If PASS, freeze exact spec and proceed to supersevere/regimes/tails/concentration/benchmark/reproducibility before holdout. If FAIL, reject permanently without repair.
