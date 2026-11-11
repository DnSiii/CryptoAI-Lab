# V98 B0 — preregistered causal adaptive overlay (2026-11-11)

Status: NEW UNTESTED successor hypothesis, NOT A3 rescue, NOT promoted. Frozen A3 code/outputs unchanged. No V14/V15/V99 consultation, no 2026+ data, no Phase083 holdout.

## Hypothesis
A composed seven-slot engine can improve long-run compounded growth by allowing a volatility-relative regime router and portfolio-equity-responsive risk governor to adapt *without* relying on the A3 absolute 3.5% hourly-volatility trigger. This B0 overlay is a distinct architectural experiment; it is not a claim of improved performance. Four existing sleeves remain independent contributors; a future integrated B0 generator must explicitly declare their immutable definitions and budgets before any economic run.

## Fixed mechanism, preregistered before economic evaluation
At completed bar t, for each asset compute the RMS hourly log return over 168 completed bars. Compare it to the median of the prior 12 **nonoverlapping** completed 168-hour RMS windows (excluding current window). Router multiplier = 0.5 when current RMS > 2 times that historical median, otherwise 1.0. Require all 13 windows, strictly positive closes, finite inputs; insufficient history -> zero new risk (fail closed), not a retrospectively selected threshold.

Governor uses portfolio equity at the completed bar t and the highest completed-bar equity observed up to t, including t. Drawdown d = 1 - equity/peak. Governor multiplier = 1.0 for d <= 0.10, 0.5 for 0.10 < d <= 0.20, and 0.25 for d > 0.20. Portfolio-level gross cap remains 0.75 and per-asset cap 0.40; cash is permitted. Never use current open/close of execution bar t+1 to decide weights. Risk reduction is a survival constraint, not the optimization target.

## Gates
First run deterministic causal/edge tests, then integrate all seven slots and native Clean-4 funding with a new B0-namespaced replay. Preserve chronological folds and predefine the independent validation source and untouched period before viewing results. Evaluate 1x/2x/4x costs, annual/regime PnL, drawdown/tails, concentration, PF, payoff, win rate, positive days and marginal contribution to complete portfolio. Reject B0 if it fails robust portfolio economics; do not change thresholds after observing failures. A3 remains an unpromoted frozen reference, not a tuning oracle. No comparison to external engines before internal freeze and independent validation.
