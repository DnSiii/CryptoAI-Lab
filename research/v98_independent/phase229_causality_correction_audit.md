# V98 Independent — Phase229 causality correction audit

Status: **PRE-HARVEST IMPLEMENTATION DEFECT FOUND; PRIOR RUN INVALID FOR SCIENTIFIC DECISION**

## Scope
V98 Independent only. No V16/V99/paper/holdout state is used or modified.

## Independent audit finding
The preregistration freezes the information set at `t-1` for a decision executed at `open(t)`. In the first Phase229 evaluator implementation, the loop inserted the return `open(t)/open(t-1)-1` into bucket history immediately before forming the signal at `open(t)`. That return requires `open(t)` and therefore was not available strictly before the execution price. The implementation comment claiming histories contained only information strictly earlier than `t` was incorrect.

This is a causal implementation defect, not a hypothesis result. Any output generated from evaluator blob `20ce9321b92d3e414c941763d1feb337a90ca36c` is quarantined and MUST NOT be interpreted, compared, promoted, rejected, or used to tune Phase229 or any later V98 hypothesis.

## Correction
Commit `269f056f78a8c3b2dfd2b67df08896da02df698d` changes the history update so that, before the decision at `open(t)=idx[i]`, the newest sample admitted is `idx[i-2] -> idx[i-1]`, keyed by the start bucket `idx[i-2]`. Thus all bucket samples end no later than `open(t-1)`.

No preregistered economic parameter changed: universe, bucket families, lookbacks 12/24, holdings 1/4, sign rule, folds, funding treatment, gross cap, or costs 7/14/28 bp are unchanged. This is solely enforcement of the already-frozen causal information set.

## Reproducibility / decision rule
Only a fresh deterministic double-run from the corrected evaluator is decision-eligible. The old in-flight workflow, if it finishes or commits a result, is explicitly superseded/quarantined. Corrected output must still pass byte-identical reproduction, firewall `<2026-01-01`, payload SHA validation, cost monotonicity, annual 2023/2024/2025 gate, and mandatory concentration/tail/regime diagnostics.

Champion remains unchanged. Holdout 2026+ remains untouched.
