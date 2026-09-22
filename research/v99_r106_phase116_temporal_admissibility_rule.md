# V99 R106 Phase116 — temporal admissibility rule (pre-result)

This rule is fixed while the Phase116 mark/index DATA AUDIT is still running and before any basis value, return relation, or candidate PnL is observed.

## Existing immutable selection requirement
The current R106 `stable_train` promotion gate requires:
- at least 3 eligible chronological temporal folds;
- at least 3 healthy folds;
- existing minimum active-hour requirements;
- no fold-boundary changes for a candidate.

## Phase116 admissibility decision rule
After Phase116 publishes paired mark/index availability:
1. Map each symbol's paired availability to the existing four chronological train folds.
2. A later mark/index-derived alpha is research-admissible only if the paired source can plausibly supply the existing minimum active hours in at least 3 folds without fill, interpolation, prehistory synthesis, or altered fold boundaries.
3. If fewer than 3 folds can be supported, close the family for R106 without running a PnL candidate.
4. Passing this data/admissibility check does **not** authorize a specific signal. A Phase117 hypothesis must still be separately preregistered, with one fixed economic mechanism, transformation, direction, horizon and causal lag before PnL.
5. No result from Phase113 may be used to choose the Phase117 sign or to invert a failed premium-level signal.

V16 Frozen and V99 Frozen remain immutable. Holdout market values remain untouched.
