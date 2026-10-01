# V98 Independent — Phase203 decision

Status: **REJECT_FAMILY_NO_RESCUE**

Family: directional efficiency / path persistence.

Evidence harvested from the frozen Phase203 run on training-only data (<2026-01-01):

- The deterministic workflow completed successfully and produced identical report hashes across two executions (`cbf9fa115b40621b04b5ba84449126e4df82f300cc85367b13d01b7186737807`).
- Temporal firewall passed on all five canonical 1h series. Validation/final holdout remains unopened.
- The representative low-threshold 24h/3h spec is negative in 2023, 2024 and 2025 under base costs. 2023 base: return -45.45%, PF 0.844, MDD -50.50%, win rate 20.66%, positive days 27.67%. 2024 base: return -52.59%, PF 0.845, MDD -53.15%, win rate 22.44%, positive days 29.78%. 2025 base is also negative overall despite an isolated bull-regime PF slightly above 1.
- Severe and supersevere costs materially worsen an already negative base mechanism; this is not a cost-only failure.
- Asset-level returns are broadly negative rather than driven by one instrument. Concentration is modest (~20–24% max in the representative folds), so removing a single loser would not rescue the family.
- Regime decomposition is broadly weak. A local regime cell near/above PF 1 is insufficient because whole-fold and multi-fold gates fail.
- Tail fields in the evaluator are dominated by the fixed transaction-cost debit (`tail_p01 == tail_p99` in displayed representative cells), so they are not evidence of a hidden positive price-return tail. This pathology is recorded rather than optimized around.

Decision: reject Phase203 as a family. No threshold rescue, inversion, regime cherry-pick, asset deletion, or holdout inspection is permitted.

Next research direction must be scientifically distinct and preregistered before execution. Priority: a causal, time-series feature family that measures **relative volatility expansion with directional close-location confirmation** rather than path efficiency, range-position reversal, volume shock, or volatility-compression breakout. Keep the grid small and frozen; retain 2023/2024/2025 chronological folds, base/severe/supersevere costs, funding, regime/tail/concentration diagnostics and deterministic reproduction.
