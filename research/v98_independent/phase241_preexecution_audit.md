# V98 Independent Phase241 — pre-execution audit

Phase241 preregistration is frozen before observing any Phase241 performance. Independent audit confirms the family is orthogonal to Phases236–240: it uses lagged quote-volume abnormality and lagged 24h price confirmation rather than residual moments, persistence, or residual shocks.

## Frozen invariants
- Training/evaluation only through 2025-12-31; 2026+ holdout remains unopened.
- Decision at open(t) uses only information available through t-1.
- Volume history uses lagged rolling median/MAD; no contemporaneous rolling baseline.
- Grid remains exactly vw {168,336}, k=1, H {4,8}: four specs.
- Dollar-neutral, gross <= 1, no regime gate.
- Costs fixed at 7/14/28 bp per unit turnover and PIT funding retained.
- Annual chronological folds 2023, 2024, 2025.
- Required diagnostics: return, max drawdown, PF, payoff, win rate, positive days, turnover, funding, tails, asset contribution/concentration, bull/bear/sideways.
- Mechanical promotion gate is unchanged from preregistration; deterministic rerun and independent validator required.

No sign flip, threshold search, asset deletion, regime rescue, parameter expansion, V99 evidence, or opened-holdout tuning is permitted after results.

Status: PREEXECUTION_AUDIT_PASS. No Phase241 performance observed.