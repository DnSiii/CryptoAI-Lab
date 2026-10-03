# V98 Independent — Phase225 execution audit

Status: **EXECUTION_LAUNCHED — RESULT BLIND**. Holdout 2026+ remains CLOSED.

This audit was written after the frozen evaluator/validator and execution workflow existed, while the first Phase225 workflow was still running and before any Phase225 result was harvested.

## Frozen execution chain
- Training-only canonical prices are rebuilt from the existing V98 Phase050 configuration.
- Price and realized-funding inputs hard-fail on timestamps >= 2026-01-01, duplicates, or non-monotonic timestamps.
- Exactly 8 preregistered specs are enforced in workflow source: V {2.0,3.0} x residual |R| {0.015,0.025} x H {4h,8h}.
- Costs remain base/severe/supersevere = 7/14/28 bp.
- Two evaluator runs from identical inputs must be byte-identical before the result can be committed.
- The independent validator checks deterministic payload SHA, exact 2023/2024/2025 folds, exact stress set, tail ordering, five-asset attribution, three BTC regimes, monotonic cost degradation, and the frozen training gate.

## Failure mechanisms to inspect after harvest
1. **Tail asymmetry:** abnormal-volume reversal may systematically fade liquidation cascades too early; inspect p01/p05 versus p95/p99 and worst trade, not only PF.
2. **Concentration:** a positive aggregate can be invalid if dominated by one asset; inspect max asset concentration and signed contribution in each year/stress.
3. **Regime dependence:** isolated bull/bear/sideways success cannot rescue a family that fails the all-year preregistered gate.
4. **Sparsity:** high V/R thresholds may fail >=30 closed trades/year; this is a preregistered failure, not permission to lower thresholds.
5. **Cost fragility:** severe and supersevere returns must not improve versus base; deterioration magnitude is diagnostic even if base already fails.
6. **Chronological causality:** signal is completed t-1 information, entry is open(t), exit is open(t+H); no same-asset overlap and gross exposure <=1 remain invariants.

## Mechanical disposition
No threshold, horizon, asset, year, regime, tail exclusion, or cost model may be changed after seeing Phase225 results. If survivor_count is zero, close as `REJECT_FAMILY_NO_RESCUE` and move to a scientifically distinct preregistered family. If one or more survive, perform full concentration/tail/regime and reproducibility audit before any holdout protocol is even considered.
