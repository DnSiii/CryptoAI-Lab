# V98 Independent Phase222 — pre-result execution semantics audit

Status: **PRE-RESULT / HOLDOUT CLOSED / NO PARAMETER CHANGES**.

This audit is based only on the frozen Phase222 preregistration and evaluator implementation. No Phase222 result payload and no timestamp >= 2026-01-01 UTC was inspected.

## Confirmed invariants

- Universe is exactly BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- Folds are calendar 2023, 2024, 2025; loader rejects any price or funding timestamp >= 2026-01-01 UTC.
- Exactly eight frozen specs: c in {0.55,0.70}, hold in {4,8}, direction in {continuation,symmetric}.
- Signal features shift completed-bar high/low/close before rolling calculations; current-bar high/low/close do not enter the trigger. Current open is the execution observation.
- Gross exposure is normalized to <=1 and same-asset overlapping entries are prohibited.
- Base/severe/supersevere costs are 7/14/28 bp per unit turnover; PIT funding is charged against lagged open exposure.
- Required portfolio metrics, stress variants and bull/bear/sideways diagnostics are emitted.

## Independent failure-risk audit

Two reporting semantics require explicit caution before any promotion decision:

1. `asset_returns` in the evaluator is a compounded standalone PnL series for each asset. It is useful for concentration diagnostics but is not an additive arithmetic attribution of portfolio return. It must not be interpreted as exact additive return contribution.
2. The current event-tail construction sums the **whole portfolio** PnL over each event's holding interval. When positions overlap across assets, the same portfolio PnL can therefore appear in multiple event observations. Those p01/p05/... tails are conservative/descriptive portfolio-window tails, not clean per-trade asset-attributed tails. They must not be used as a promotion-positive argument until an attribution-safe implementation is validated.

Neither issue changes signals, parameters, costs, folds or the mechanical training gate. Therefore they do not justify a rescue or parameter edit. They are recorded before result harvesting so that any later interpretation cannot silently redefine the evidence.

## Decision discipline

The mechanical gate remains exactly preregistered: base return > 0 and base PF > 1 in each of 2023/2024/2025. Zero coherent specs means `REJECT_FAMILY_NO_RESCUE`. A pass only authorizes a separately preregistered robustness stage; it does not authorize opening 2026+.

The strengthened namespaced validator additionally verifies the evaluator's internal deterministic payload SHA, metric domains, regime metric completeness, stress monotonicity, exact fold/stress sets, and optional byte-identical reproduction.
