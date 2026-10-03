# V98 Independent Phase223 — pre-execution code audit v2

Status: **PASS_FOR_EXECUTION** (result-free audit)

Performed after Phase222 was closed as INVALID_DESIGN_STRUCTURAL_TRIGGER and before any Phase223 result was observed. Holdout >= 2026-01-01 remains unopened.

## Frozen-spec fidelity

Evaluator matches the preregistered Cartesian grid exactly: W={168,336}, K={2.5,3.5}, H={2,6}, total 8 specs. Universe is BTCUSDT/ETHUSDT/BNBUSDT/XRPUSDT/SOLUSDT. Costs remain 7/14/28 bp per unit turnover.

## Causality / execution

`r1` and rolling sigma are both formed from completed close returns and shifted so the decision at t uses information through t-1 only. Position is written beginning at t, while PnL uses `weight.shift(1) * open.pct_change()`, so the first realized return occurs from open(t) to open(t+1); this is consistent with execution at open(t) and avoids earning the already-observed t-1 shock. Current high/low/close(t) do not enter the signal.

## Market filter fidelity

The implementation rejects a candidate only when shock sign equals BTC completed-return sign and |BTC r1| >= 0.75%, exactly matching the frozen preregistration. Although the family name says idiosyncratic, the preregistration operationally defines idiosyncrasy via the explicit broad-market jump filter rather than beta residualization; implementation therefore must not be changed now to residualize against BTC.

## Exposure / overlap

Same-asset overlap is prevented by `until[a]`. Simultaneous assets are normalized to equal absolute weights and gross exposure is asserted <=1. No leverage is introduced.

## Costs, funding, tails

Turnover is charged from absolute weight changes, including entry/rebalance/exit. Funding is applied to lagged exposure. Closed-trade tails are asset-attributed and include the exit/rebalance row, while fold-boundary-censored trades are excluded from tail statistics. Per-asset PnL contributions and max-asset concentration are additive diagnostics.

## Remaining execution requirements

A decision-grade run must: rebuild training-only inputs; execute twice; verify byte-identical output and deterministic payload SHA; validate metric domains; validate stress monotonicity; report regimes/concentration/tails; then apply the frozen gate (base return >0 and PF>1 in each 2023/2024/2025). No rescue is permitted if zero specs pass.
