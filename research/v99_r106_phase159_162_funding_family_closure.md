# V99 R106 — Phase159–162 Funding Relative-Value Family Closure

Decision recorded after Phase162 TRAIN result and before Phase163 PnL.

## Evidence
- Phase159 level dispersion: TRAIN rejected, 0/4 healthy folds.
- Phase160 first-difference dispersion: TRAIN rejected, 0/4 healthy folds.
- Phase161 acceleration dispersion: TRAIN rejected, 0/4 healthy folds.
- Phase162 level/change interaction: TRAIN rejected, 0/4 healthy folds; ROI -58.52%, PF 0.8688, max drawdown 62.18%, robust mean excluding top 1% -0.014892%/h.

## Failure mechanism assessment
The failure persists across level, first difference, second difference, and level×change interaction while using the same deterministic funding archive, causal shifted normalization, execution lag, severe-cost evaluator, and temporal-fold discipline. This is evidence against continuing to mine cross-sectional funding relative-value transforms in the current five-asset universe. The negative robust mean and 0/4 healthy folds in Phase162 argue against a result driven only by a few adverse tails.

## Research decision
Close the cross-sectional funding relative-value family. Do not rescue it with thresholds, alternative lookbacks, asset subsets, sign flips, cost relaxation, or post-hoc parameter searches. Phase163 changes the estimand to a market-wide directional crowding state (cross-asset median funding), which preserves the data source but tests a distinct economic mechanism and portfolio geometry.

Holdout remains untouched. V16 Frozen and V99 Frozen remain immutable.
