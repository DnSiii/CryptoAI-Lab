# V99 R106 Phase122 — aggressive trade-count imbalance — preregistration

Status: PREREGISTERED BEFORE ANY PHASE122 PNL.

## Scientific motivation
Phase120 tested signed aggressive *notional* imbalance and failed broadly. Phase121 tests pressure restricted to causally-defined large trades. Phase122 is deliberately distinct: it asks whether the *number* of buyer-initiated versus seller-initiated aggressive prints contains information that notional weighting obscures. This is a microstructure participation/intensity hypothesis, not a size-pressure hypothesis.

## Frozen hypothesis
For each symbol and UTC hour t, using Binance Futures aggTrades strictly before the execution bar:

- `buy_count_t`: count of buyer-initiated aggressive aggTrades in hour t.
- `sell_count_t`: count of seller-initiated aggressive aggTrades in hour t.
- `count_imbalance_t = (buy_count_t - sell_count_t) / max(buy_count_t + sell_count_t, 1)`.
- Cross-sectionally robust-standardize count_imbalance at each hour using the same deterministic robust-z convention already used by the R106 research harness, then squash with `tanh`.
- The resulting alpha is shifted exactly one full bar (`t-1`) before execution. No contemporaneous execution is permitted.

Direction is frozen as continuation: positive aggressive trade-count imbalance => positive alpha; negative => negative alpha. No sign flip is allowed after observing PnL.

## Universe / data discipline
Use the same Phase119-integrity-qualified raw aggTrades source and the same deterministic pre-holdout universe eligibility rules used by Phase120/121. Universe construction may use availability/integrity metadata only, never returns or PnL. Minimum executable universe: 8 assets. Missing raw files are not imputed. Any observation timestamp >= 2024-01-18 is a hard abort until a candidate has passed every pre-holdout gate and is formally frozen for final holdout evaluation.

## Selection and evaluation discipline
No grid search, horizon search, sign search, threshold search, asset-by-asset parameter tuning, or post-result retuning. Chronological train-only evaluation only. The required gate order is:

1. severe-cost train gate;
2. four temporal folds;
3. supersevere-cost stress;
4. regime matrix plus tail/concentration audit;
5. benchmark-envelope comparison;
6. deterministic reproducibility/invariant rerun;
7. only if all preceding gates pass, freeze the exact candidate before any holdout access.

A failure at a mandatory gate permanently rejects this exact Phase122 hypothesis. Results from Phase120/121 may motivate scientific interpretation but may not be used to change the frozen Phase122 definition.

## Frozen assets
V16 Frozen and V99 Frozen are read-only. Workflows must snapshot/verify them before and after execution.
