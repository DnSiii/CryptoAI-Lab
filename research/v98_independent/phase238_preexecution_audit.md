# V98 Independent Phase238 — pre-execution integrity audit

Performed after preregistration and implementation, before any Phase238 performance output was generated or inspected.

- Preregistered grid and evaluator grid both contain exactly 8 specs: beta {168,336} × autocorrelation window {72,168} × H {4,8}, k=1.
- Direction matches preregistration: long highest lag-1 residual autocorrelation, short lowest.
- Residual construction uses `beta.shift(1)`; rolling autocorrelation is computed from residual history and the trading loop consumes `signal.iloc[i-1]` for the open(t) decision.
- Evaluation folds are exactly 2023, 2024, 2025; cutoff firewall is `<2026-01-01` for both prices and funding.
- Costs remain 7/14/28 bp per L1 turnover; point-in-time funding and gross<=1 invariant are retained.
- Required DD, PF, payoff, win rate, positive days, turnover, tails, asset concentration, funding and bull/bear/sideways diagnostics are emitted.
- Independent validator enforces exact grid/folds/cost sleeves, finite payload, cost monotonicity and the existing annual gate without rescue.
- No Phase238 result existed or was inspected at the time of this audit. 2026+ remains unopened.

Phase238 is therefore eligible for decision-grade execution with deterministic double-run/SHA verification. Any implementation change affecting hypothesis, grid, direction, causality, folds or gate requires a new preregistration rather than silent modification.
