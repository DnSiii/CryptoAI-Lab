# V99 R106 Phase135 pre-execution integrity audit — 2026-09-25

## Decision

Phase135 remains preregistered but is **NOT cleared for execution** yet.

## Audit finding: holdout parse invariant

The Phase135 preregistration states both:
- no holdout rows may enter feature construction; and
- holdout must not be parsed or used for selection.

The current runner satisfies the first requirement by constructing `ct` and `vt` strictly on timestamps before `2024-01-18 00:00:00 UTC`, shifting the complete score by one hour, and forcing all post-train targets to zero.

However, the runner obtains `data` through `v15_setup()` before truncation. That setup returns the full canonical dataset, after which the runner slices it. Therefore the emitted field `holdout_not_parsed: true` is stronger than the implementation can currently prove. This is an integrity/metadata defect even though holdout rows do not enter feature construction or train selection.

## Required correction before PnL

Do not execute Phase135 until one of these is implemented and audited:

1. preferred: a train-bounded canonical loader/replay that never loads rows at or after TRAIN_END; or
2. a deterministic train-only data view created immediately at ingestion, with the report wording corrected to the strictly provable invariant (holdout not used for feature construction, selection, or diagnostics), **only if** project protocol defines "untouched" as no analytical use rather than no parsing.

No PnL was observed in discovering this issue. The frozen 72h/168h hypothesis, direction, gross, costs, folds and gate remain unchanged. This correction is infrastructure/integrity work and must not alter the hypothesis.

## Other invariants rechecked

- score is shifted exactly one hour after the full coupling transform;
- feature inputs are sliced to timestamps strictly before TRAIN_END;
- portfolio L1 is capped at 1 before alpha gross 0.20;
- post-train targets are explicitly zero;
- four temporal folds come from the existing Phase47 diagnostic contract;
- no grid, sign flip, threshold search, or alternate horizon is permitted;
- V16 Frozen and V99 Frozen are not write targets.

## Workflow status

A protected Phase135 workflow creation attempt was blocked by the connector safety layer. This is secondary to the holdout-parse finding: Phase135 should not be launched even if workflow creation becomes available until the invariant above is resolved.
