# V98 Independent — Phase234 postmortem

Decision: **REJECT_FAMILY_NO_RESCUE**.

Scope: Phase234 idiosyncratic-volatility relative-value only. Holdout >=2026 remains unopened. No V16/V99 state is touched.

## Integrity / reproducibility
- Decision-grade workflow run 37261017455 completed successfully.
- Training-only rebuild completed; the explicit holdout firewall check passed.
- Frozen-grid invariant check passed before evaluation.
- Two independent evaluator executions produced byte-identical canonical report SHA256 `b49844841872cb34231b2bc69a252417227a11bd11c85fb285a673f992f215e9`.
- Mechanical validator returned `REJECT_FAMILY_NO_RESCUE`.

## Economic failure mechanism
The family failed before any holdout access. The preregistered requirement was annual robustness across the chronological 2023/2024/2025 folds after realistic funding/cost accounting and under the severe/supersevere schedule. No rescue, parameter expansion, fold dropping, or post-result tuning is permitted. Because the mechanical validator rejected the frozen family, Phase234 is closed rather than mined for a favorable subperiod/spec.

## Stress / pathology interpretation
The evaluation contract includes 7/14/28 bp cost cases plus max drawdown, Profit Factor, payoff, win rate, positive-day fraction, regime diagnostics, concentration and tail diagnostics. A family that cannot clear the frozen annual gate has no scientific basis for promotion regardless of isolated descriptive metrics. The correct action is rejection and movement to a preregistered orthogonal family.

## Decision
**REJECT_FAMILY_NO_RESCUE.** Champion unchanged. Phase235, if pursued, must remain independent and use only its own preregistered information set.