# V98 Independent — Phase197 training decision

## Scope / isolation
- Branch: `research/v98-independent-zero` only.
- Evidence: `reports/v98_independent_phase197_dispersion_momentum.json` harvested by commit `7b3670c153c00225980de2ea40893d6675470740`.
- Engine namespace: V98 Independent only.
- Final holdout remains unopened (`final_holdout: null`). No V16/V99 state, workflow, report, or paper evidence is used for selection.

## Decision
**REJECT_FAMILY_NO_RESCUE.** No Phase197 spec is promoted.

## Evidence and failure mechanism
The most economically interesting visible member, `lb24_q60_h12`, has positive aggregate base economics (total return +66.11%, daily PF 1.131, MDD -32.27%, payoff 1.374), but fails chronological consistency and cost robustness. Its folds decay from 2023 +53.76% / PF 1.294, to 2024 +24.36% / PF 1.158, to 2025 -13.44% / PF 0.910. This is a material temporal decay, not a stable edge.

Under severe costs the same spec falls to -37.11%, PF 0.945 and MDD -52.42%; under supersevere it falls to -86.65%, PF 0.720 and MDD -89.63%. Therefore the base result is too dependent on friction assumptions for promotion.

Regime breadth is also incomplete: approximate bear contribution is negative (-0.0999) while bull is strongly positive (+0.6789), indicating substantial regime dependence. Tail concentration does not offer a legitimate rescue: bottom-10 negative days account for only ~9.69% of negative loss mass, so removing a handful of observations would not explain the failure; top-10 positive share ~17.66% also shows gains are not solely one lucky day cluster.

The shorter `lb24_q60_h6` member is weaker: base PF 1.047, MDD about -49.96%, with negative approximate bear and sideways contributions. This supports the family-level conclusion rather than a parameter-local accident.

## Integrity / anti-overfit ruling
- Workflow completed successfully after canonical training-only rebuild and explicit pre-2026 assertions.
- The workflow executed Phase197 twice and required byte identity before committing the report.
- No post-hoc inversion, fold deletion, tail deletion, cost weakening, or parameter rescue is permitted.
- Phase197 is closed. Any next experiment must be preregistered as a scientifically distinct hypothesis before execution.
