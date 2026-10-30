# V98 Independent Phase222 — structural validity audit

Status: **INVALID_DESIGN / do not interpret as negative alpha evidence**

This audit was performed after workflow run 37127481356 failed at the validator invocation, but before any valid Phase222 result was harvested. No 2026+ holdout data were opened and no V99 evidence was used.

## Finding 1 — frozen breakout trigger is structurally degenerate on continuous hourly OHLC

The frozen evaluator computes `prior_hi(t)` as the rolling maximum of `high` over completed bars through `t-1`, and triggers long only when `open(t) > prior_hi(t)` (short analogously with `open(t) < prior_lo(t)`). In standard continuous crypto OHLC, `open(t) = close(t-1)` absent a data discontinuity, while `low(t-1) <= close(t-1) <= high(t-1)`. Because `high(t-1)` and `low(t-1)` are included in the rolling extrema, the strict inequalities cannot occur on a continuous series. Any observed trigger would therefore be driven by a gap/discontinuity, timestamp mismatch, or data-quality event rather than the intended intraday breakout mechanism.

This is a design-level contradiction, not a performance result. Phase222 must not be rescued by silently changing the trigger to current high/low or another rule after seeing outcomes. Such a change would define a new preregistered family.

## Finding 2 — failed workflow is non-evidentiary

Run 37127481356 failed before decision-grade validation because the workflow passed two positional result paths to a validator whose CLI accepts only one positional path plus optional flags. The branch now contains the corrected workflow syntax, but rerunning the old job would execute its old commit and therefore does not validate the correction.

## Disposition

Phase222 is closed as `INVALID_DESIGN_STRUCTURAL_TRIGGER`, not `REJECT_ALPHA`. It is excluded from champion comparison and from counts of scientifically tested alpha families. No parameter rescue is allowed. The next valid work item is the already preregistered, orthogonal Phase223 family, preserving its frozen eight-spec grid and all original gates.

## Integrity constraints retained

- chronological folds: 2023 / 2024 / 2025
- holdout: all timestamps >= 2026-01-01 remain unopened
- realistic funding and base/severe/supersevere costs
- max drawdown, Profit Factor, payoff, win rate, positive days
- regime, concentration and clean trade-tail diagnostics
- deterministic payload/reproducibility checks
- no V99 tuning or selection
