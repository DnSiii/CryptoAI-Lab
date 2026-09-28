# V99 R106 — Phase169–174 macro family closure

Date: 2026-09-28

## Decision

The external daily macro family tested in Phases169–174 is closed for rescue/retuning. Phase174 was the sixth scientifically distinct formulation in this family and was rejected at the TRAIN-only alpha gate.

Observed Phase174 diagnostics under severe costs: ROI +0.5408%, PF 1.00895, max drawdown 1.2472%, positive-hour ratio 50.54%, robust mean after removing top 1% = -5.53e-06, healthy temporal folds 0/4. This repeats the Phase169–173 pathology: aggregate PnL can be slightly positive while the robust tail-stripped mean is negative and temporal folds fail.

## Failure mechanism

The evidence is consistent with sparse favorable crypto tails carrying apparent macro PnL rather than a persistent, temporally transferable macro edge. Persistence, acceleration, breadth, curve/liquidity shock and interaction formulations did not repair the fold/tail pathology. Therefore changing lookbacks, thresholds, weights, signs or z-score definitions inside the same daily FRED panel would constitute rescue tuning and is prohibited.

## Scientific consequence

No Phase169–174 candidate is promoted. No holdout observation was used for feature construction or selection. V16 Frozen and V99 Frozen remain untouched. The next hypothesis must be orthogonal to this daily macro-panel family rather than another parameterization of it.

## Preserved invariants

- causal t-1 execution;
- chronological TRAIN-only selection;
- untouched holdout;
- temporal-fold gate;
- severe/supersevere cost discipline;
- no benchmark-envelope or regime gate bypass;
- no post-result sign/threshold/window rescue;
- reproducibility and frozen-asset firewalls.
