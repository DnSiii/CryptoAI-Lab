# V99 R106 Phase194 USDC causal economic hypothesis preregistration

Status: PREREGISTERED, TRAIN_ONLY, economic_trials=0.

Rationale: Phase193 passed only the DATA_ONLY source-quality gate for USDC native Mint/Burn. Phase194 is the first economic test and must not reinterpret Phase193 diagnostics as alpha.

Immutable discipline:
- Do not modify V16 Frozen or V99 Frozen.
- Reuse the frozen Phase192 snapshot and Phase193-approved USDC Mint/Burn source only.
- Preserve chronological TRAIN-only model/threshold selection, temporal folds, untouched holdout, severe/supersevere costs, regime matrix, benchmark envelope, reproducibility, and existing anti-overfit gates.
- Holdout remains inaccessible until every preregistered TRAIN gate passes.
- No post-result threshold/window/direction edits.

Hypothesis H194:
A strictly causal net issuer impulse feature, computed as Mint amount minus Burn amount over fully closed 24h source intervals, may add independent information to the existing R106 engine. At decision bar t, the newest eligible source interval must have closed strictly before t; no same-bar or future source event may enter.

Fixed transform:
1. USDC decimals = 6.
2. Aggregate signed native amount in fixed UTC 24h buckets.
3. At each decision bar use only completed buckets available at t-1.
4. Normalize using expanding TRAIN-only history available before the decision bar; no full-sample statistics.
5. Primary signal is the sign of the expanding z-score. Magnitude thresholds are not permitted in this first trial.
6. Evaluate the signal as an additive/veto candidate under the existing engine protocol, never by changing the baseline engine after observing results.

Required TRAIN gates before any holdout:
- causal leakage/invariant test;
- deterministic rebuild/replay;
- chronological temporal-fold stability;
- severe and supersevere cost survival;
- regime-matrix non-collapse;
- benchmark-envelope comparison;
- tail/concentration attribution;
- no single fold/regime dominating claimed improvement.

Decision rule:
Reject H194 if it fails any existing mandatory TRAIN gate. Passing TRAIN gates permits only the already-established untouched-holdout procedure; it does not itself promote V99.
