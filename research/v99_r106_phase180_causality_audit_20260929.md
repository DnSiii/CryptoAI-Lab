# V99 R106 Phase180 — causal-lag audit (2026-09-29)

## Scope
TRAIN/data-feature path only. No PnL, benchmark selection, temporal-fold scoring, or holdout data was inspected. V16 Frozen and V99 Frozen are out of scope.

## Finding
The first Phase180 feature builder attached a rolling inter-block statistic to block `h` after appending the delta `(time[h]-time[h-1])`. That is internally reproducible, but it did **not** structurally enforce the project's extra t-1 rule: correctness depended on every downstream consumer remembering to lag the feature again.

This is a causal-boundary weakness, especially because Bitcoin header `time` is a miner-declared consensus timestamp rather than a precise observation-arrival timestamp. A future evaluator could accidentally consume a same-row statistic and silently erase the intended safety margin.

## Remediation
The builder now materializes row `h` from deltas whose newest endpoint is `h-1`, then appends the delta ending at `h` only after row `h` is complete. The build manifest declares `causal_lag_blocks: 1`.

Tests explicitly require:
- changing `time[h]` cannot change feature columns on row `h`;
- the perturbation becomes visible only from row `h+1`;
- warm-up shifts consistently with the structural lag;
- last-row timestamp mutation cannot change its own feature vector;
- output remains byte reproducible;
- gate SHA, PASS status and holdout firewall remain fail-closed.

## Decision
Phase180 remains **DATA/FEATURE-only, not admitted to alpha/PnL**. Admission still requires a real TRAIN + required pre-roll header dataset to pass the consensus/data gate, deterministic feature build, temporal coverage checks, and reproduction. Only after those gates may a preregistered train-only alpha hypothesis be evaluated under the existing temporal folds, severe/supersevere costs, regime matrix and benchmark envelope.
