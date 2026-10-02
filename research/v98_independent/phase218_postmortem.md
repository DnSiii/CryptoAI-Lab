# V98 Independent — Phase218 post-mortem

## Decision
REJECT_FAMILY_NO_RESCUE.

Phase218 (realized-volatility term structure) completed successfully under the frozen eight-spec grid. The mechanical training-fold gate reported zero coherent specifications across 2023/2024/2025. Reproducibility was byte-identical in the workflow (`179eb5bf80798fd61c66b6f8b00f9fcebb31b8bc981870402b240f9a37b14404` for both serialized runs); firewall, static causality, schema and monotonic stress invariants all passed.

## Failure audit
The representative `rvts_V125_R050_hold3` is decisively uneconomic in 2023 base: return -81.53%, max drawdown -85.06%, PF 0.8481, payoff 1.3111, win rate 17.48%, positive days 32.05%, 2,146 trades. Severe worsens to -94.18%, MDD -94.96%, PF 0.7557. All four asset sleeves are negative in base, and bull/bear/sideways regime returns are all negative. This is broad failure rather than one-asset or one-regime concentration.

The payoff above 1 does not rescue the family: hit rate is too low and turnover/cost sensitivity is severe. The negative median trade/tail center and monotonic deterioration under cost stress are consistent with insufficient gross edge rather than a narrow execution artifact. No sign inversion, regime filter, asset exclusion, threshold rescue, or hold-period rescue is permitted post hoc.

## Integrity
- Data firewall remains `<2026-01-01`; final holdout remains unopened.
- Signal construction is causal (`pct_change(fill_method=None)`, rolling windows, shift before entry).
- Exactly eight preregistered specs were evaluated.
- Base/severe/supersevere costs and PIT funding were retained.
- Required MDD, PF, payoff, win rate, positive days, tails, concentration and regime diagnostics were emitted.
- No V16/V99 state or V99 evidence was used for selection.

## Consequence
Phase218 is rejected as a family. Champion status is unchanged. The next experiment must be scientifically distinct and preregistered before implementation.
