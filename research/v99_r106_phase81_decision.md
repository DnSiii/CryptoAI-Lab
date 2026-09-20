# V99 R106 Phase81 — decision

Status: **PERMANENT TRAIN-ONLY REJECTION**.

Phase81 tested the preregistered continuation feature `log(sum_toptrader_long_short_ratio / count_long_short_ratio).shift(1)` at alpha gross 0.20 under severe costs, with chronological train-only evaluation and the frozen temporal-fold/robustness gate.

Observed train diagnostics: ROI **+1.9242%**, profit factor **1.0088**, max drawdown **6.6652%**, robust mean excluding top 1% **-3.1355e-05**, and **0/4 healthy temporal folds**. Therefore `stable_train=false` and no candidate was selected.

The exact Phase81 hypothesis is rejected permanently. No sign flip, lag/horizon change, smoothing, threshold, weighting grid, gross grid, symbol rescue, or post-result retuning is permitted.

The untouched holdout was not parsed or inspected. V16 Frozen and V99 Frozen remain untouched.

Per the already-frozen contingent preregistration, Phase82 (TOP-CAPITAL vs TAKER-FLOW divergence) is now authorized to run unchanged. If Phase82 passes train-only, its exact specification must be frozen before supersevere-cost, regime-matrix, benchmark-envelope and reproducibility gates; holdout remains forbidden until those gates are satisfied.
