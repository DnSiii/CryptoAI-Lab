# V99 R106 Phase135 pre-execution integrity audit — 2026-09-25

## Decision

Phase135 is **CLEARED FOR TRAIN-ONLY EXECUTION** after the provenance contract was corrected to match what the runner can actually prove.

No Phase135 PnL was inspected during this correction. The frozen 72h/168h hypothesis, direction, gross, costs, folds and train gate remain unchanged.

## Holdout provenance correction

The earlier audit correctly identified an over-strong metadata claim: the canonical V15 setup may materialize the full panel before the Phase135 runner truncates feature inputs to timestamps strictly before `2024-01-18 00:00:00 UTC`.

The project-wide V99 protocol defines untouched holdout operationally as **no analytical use for feature construction, fitting, selection, diagnostics, parameter choice, or promotion**. It does not require the shared canonical loader to be physically incapable of materializing later rows.

The Phase135 preregistration and runner were therefore aligned to the strictly provable contract:

- `canonical_replay_may_materialize_full_panel: true`;
- `holdout_rows_used_for_feature_construction: 0`;
- `holdout_rows_used_for_selection: 0`;
- feature frames `ct` and `vt` are hard-cut to `index < TRAIN_END` before returns, dollar-volume surprise, rolling coupling, robust cross-sectional normalization, or score construction;
- the complete alpha is shifted exactly one hour;
- all targets at and after `TRAIN_END` are explicitly zero before evaluation.

This correction changes metadata/provenance wording only; it does not change the scientific hypothesis.

## Rechecked invariants

- train end exclusive: 2024-01-18 00:00:00 UTC;
- feature input max timestamp must be strictly before train end;
- 72h coupling state and 168h dollar-volume baseline remain frozen;
- robust cross-sectional transform requires at least 8 assets;
- score direction remains continuation;
- alpha gross remains 0.20;
- portfolio L1 <= 1;
- selection cost remains severe;
- exactly four temporal folds use the existing Phase47 diagnostic contract;
- no sign flip, no grid, no threshold search, no alternate horizon after result;
- V16 Frozen and V99 Frozen are not write targets.

## Execution gate

Phase135 may now run the train-only gate.

- PASS: freeze this exact specification and proceed to the preregistered downstream gates (supersevere, regimes, tails/concentration, benchmark envelope, reproducibility) before any untouched-holdout evaluation.
- FAIL: permanently reject Phase135 with no rescue tuning.

The workflow, if created, must assert the corrected provenance fields rather than the obsolete `holdout_not_parsed` flag.
