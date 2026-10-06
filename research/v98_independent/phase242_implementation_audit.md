# V98 Independent Phase242 — implementation audit (2026-10-06)

Status: **IMPLEMENTED, NOT EXECUTED, NO PERFORMANCE OBSERVED**.

Scope is strictly Phase242 on `research/v98-independent-zero`. No V99 evidence/state and no 2026+ holdout information were consulted.

## Preregister-to-code invariants
- Grid is exactly four specs: impact normalization windows 168/336h, k=1 each side, holding 4/8h.
- Raw impact is `abs(r1)/max(quote_volume,1e-12)`, transformed with `log1p`.
- Rolling median/MAD use only own history ending at u-1; MAD floor is 1e-9.
- Decision at open(t) reads the score already computed at t-1. Thus r1(t-1), impact(t-1), and its normalization are known before the open(t) position is formed.
- Score is exactly `-sign(r1)*normalized_impact`; cross-sectional bottom is short and top is long, so unusually high-impact positive returns are faded and unusually high-impact negative returns are bought.
- Dollar-neutral event weights are normalized to gross <=1; no hidden leverage or asset deletion.
- PnL uses prior position against open-to-open returns, explicit L1 turnover costs, and PIT funding.
- Folds remain calendar 2023/2024/2025; price and funding loaders reject timestamps >=2026-01-01.
- Costs remain 7/14/28 bp; supersevere is diagnostic, not a tuning knob.
- Output includes DD, PF, payoff, win rate, positive days, turnover, daily tails, asset contribution/concentration, funding contribution, and bull/bear/sideways diagnostics.

## Semantic clarification frozen before execution
The preregistration prose says “high positive score means large positive impact is faded”; that phrase is sign-inverted relative to the explicitly frozen equation and rank rule. The equation/rank pair is mechanically unambiguous and takes precedence: a positive-return/high-impact observation has a negative score and therefore belongs on the short/fade side; a negative-return/high-impact observation has a positive score and belongs on the long/buy side. This is a documentation correction only, made before any Phase242 performance is observed; no formula, direction, threshold, grid, gate, asset set, or cost is changed.

## Reproducibility
A result is ineligible for promotion until two independent executions are byte-identical and the payload SHA256 is independently recomputed by the validator. Any mismatch is an execution failure, not a selection signal.
