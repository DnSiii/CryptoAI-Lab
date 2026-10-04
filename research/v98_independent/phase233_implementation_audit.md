# V98 Independent Phase233 — independent implementation audit

Audit performed after implementation and before observing any Phase233 result.

- Frozen preregistration grid is reproduced exactly: 8 `(beta lookback, residual horizon, k, hold)` specs.
- Causality: `open(t)` reads `signal.iloc[i-1]`; rolling beta/residual construction at row `i-1` contains returns ending at `open(t-1)` or earlier. No `open(t)->open(t+1)` observation enters the decision.
- Chronology/firewall: evaluator accepts only canonical/funding inputs strictly `<2026-01-01`; folds are calendar 2023, 2024, 2025. 2026+ remains unopened.
- Execution/accounting: equal long/short absolute weights, deterministic `(signal,symbol)` ranking, overlapping sleeves normalized to gross <= 1; turnover costs are 7/14/28 bp and funding cash is point-in-time delayed to the next executable hour.
- Diagnostics: return, max drawdown, PF, payoff, win rate, positive days, tails, per-asset/funding contribution, concentration, and lagged BTC bull/bear/sideways regimes are emitted. Event-tail attribution is diagnostic only; portfolio PnL is authoritative under overlap.
- Validator reproduces the existing frozen V98 annual gate and cost-monotonicity invariant. No sign flip, threshold rescue, regime filter, asset exclusion or post-result grid change is allowed.

Conclusion: implementation is eligible for decision-grade execution without opening holdout or borrowing evidence from V99.
