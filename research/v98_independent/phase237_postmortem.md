# V98 Independent Phase237 — decision-grade post-mortem

## Mechanical decision
`REJECT_FAMILY_NO_RESCUE`.

The decision-grade workflow completed successfully. Firewall/funding/causality/grid invariants passed, the evaluator ran twice with byte-identical output SHA256 `095e4106a041d324b9bc2f87aaffa4a3ff153d9a7d6006307fe8332b1e93a5b1`, and the independent validator reported zero passing specs across the frozen 8-spec grid.

## Failure mechanism
The family is not rejected because of a marginal transaction-cost miss. It fails the annual gate structurally. A representative frozen spec (`idsemi_beta168_down168_k1_h4`) is strongly positive in 2023 and 2024 even under supersevere costs, but fails in 2025: base return -1.32%, max drawdown -33.40%, PF 1.0037 and positive-days 46.03%; severe return -6.39% with PF below 1. The 2025 failure is regime-localized: bear and bull sleeves remain positive while sideways is deeply negative (base return -38.52%, PF 0.8870, DD -44.92%).

This is meaningful instability, not permission to add a regime filter. The preregistered annual gate requires every fold to pass without conditional rescue. The family also shows economically important concentration in individual asset contributions in earlier years (e.g. the representative 2023 result is dominated by SOL), reinforcing the decision not to promote on aggregate return alone.

## Integrity observations
- 2026+ remained outside the evaluation payload and was not used for tuning/selection.
- Chronological folds remained 2023/2024/2025.
- Funding was point-in-time; costs were 7/14/28 bp.
- Required DD/PF/payoff/win-rate/positive-days, tails, concentration and regime diagnostics were present.
- No sign flip, parameter rescue, threshold search or regime gating is authorized from this result.

## Research implication
Downside residual magnitude contains episodic cross-sectional structure, but the frozen direction is not stable across chronological regimes. The next experiment must therefore test a genuinely different property of residual dynamics rather than conditioning or retuning downside-semivariance.
