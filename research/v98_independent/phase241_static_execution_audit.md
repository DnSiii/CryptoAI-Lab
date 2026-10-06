# V98 Independent Phase241 — static execution audit (2026-10-06)

Status: **EXECUTION_READY_NO_PERFORMANCE_OBSERVED**.

Scope is strictly Phase241 on `research/v98-independent-zero`; no V99 or holdout evidence was consulted.

## Independent invariants
- Frozen grid is exactly 4 specs: volume windows 168/336h, k=1 each side, holding 4/8h.
- Decision at open(t) consumes `score.iloc[i-1]`; price leg is close-based r24 and robust quote-volume median/MAD are lagged one bar.
- MAD floor is 1e-9; no sign flip, rescue filter, asset deletion, regime selection, or post-result tuning exists.
- Position gross exposure is normalized to <=1.
- PnL uses prior position against open-to-open return, explicit L1 turnover costs, and PIT funding cash.
- Cost ladder is frozen at 7/14/28 bp.
- Folds are chronological calendar 2023, 2024, 2025; loader rejects any timestamp >=2026-01-01.
- Validator requires return, max drawdown, PF, payoff, win rate, positive days, turnover, daily tails, asset concentration/contribution, funding contribution, and bull/bear/sideways diagnostics.
- Mechanical promotion requires every fold positive with PF>1 under base and severe, plus base DD >= -35% and positive-days >50%. Supersevere remains mandatory stress evidence, not a hidden selection knob.

## Path audit
The holding implementation creates overlapping H-hour events and then normalizes aggregate gross exposure. This means H is a preregistered persistence/consensus horizon rather than independent unnormalized stacking. That behavior is deterministic and applies symmetrically across all assets/specs.

## Reproducibility requirement
Execution must produce two byte-identical JSON outputs before validation. Any mismatch is an execution failure, not evidence eligible for promotion.

No performance values were observed while writing this audit.
