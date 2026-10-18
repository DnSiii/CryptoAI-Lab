# V99 R106 D1 — Cycle 29: stale settlement mark guard (2026-10-17)

**Status: DATA_ONLY / HOLD / NO PROMOTION.** This is a read-only research checkpoint, not an integrated D1 engine, an economic backtest, or evidence of exchange execution.

Local review of the 45-file D1 transfer bundle revealed that a claimed settlement mark could be observed arbitrarily long before its settlement timestamp and still be accepted. This risks assigning a stale price to modeled position-specific funding. A fail-closed local correction rejects `settled_at - observed_at > 1 hour` and retains the prohibition on observations after settlement. This is a pre-economic source-quality invariant, not a retuning of the frozen D1 alpha or its cost thresholds.

**Local evidence:** 202/202 D1 synthetic unit tests passed (200 previous plus 2 new stale-mark boundary tests); five independent synthetic accounting/risk/score/cost-path oracles reexecuted. No historical TRAIN ROI, historical first-party OKX spot/perp/fill/fee certification, or independent historical rerun exists. The correction is **NOT integrated into this branch**; the full 45-file source transfer remains staged locally and requires atomic source integration and CI. This checkpoint does not grant permission to run historical economics.

**Next:** atomically integrate the complete reviewed D1 source set, including the stale-mark correction; execute CI on the exact commit; acquire and authenticate TRAIN-only first-party OKX execution/funding/fee evidence; run exactly one preregistered D1 TRAIN trial if and only if the provenance gate passes. C1/C2 remain rejected; sealed validation and final holdout remain unopened; frozen and paper records must not be modified.
