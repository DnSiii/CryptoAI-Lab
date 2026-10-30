# V98 Independent Phase236 — pre-execution audit

Date: 2026-10-05. Status: completed before observing any Phase236 result.

- Frozen preregistration reconciled exactly: 2 beta windows × 2 residual-kurtosis windows × 2 holding horizons = 8 specs; k=1 fixed.
- Direction is frozen with no rescue: long highest residual excess-kurtosis asset, short lowest.
- Causality: residual at u uses `beta.shift(1)`; decision at open(t) uses `signal.iloc[i-1]`.
- Chronology/firewall: independent 2023/2024/2025 folds; price and funding loaders reject timestamps >= 2026-01-01 UTC.
- Accounting: gross exposure normalized <=1; turnover costs applied at 7/14/28 bp; PIT funding charged from lagged held weight.
- Diagnostics: max drawdown, Profit Factor, payoff, win rate, positive days, turnover, hourly tails, best/worst day, asset contribution/concentration, funding contribution, and lagged BTC bull/bear/sideways regimes.
- Reproducibility: decision-grade workflow rebuilds training-only inputs, runs evaluator twice, requires byte-identical outputs, prints SHA256, then applies independent mechanical validator.
- Gate is unchanged from preregistered discipline: every annual fold must pass; no pooled rescue, sign flip, parameter rescue, or holdout opening after a failed training gate.

No Phase236 performance result was inspected while producing this audit. V16/V99/paper namespaces are outside the workflow write set.
