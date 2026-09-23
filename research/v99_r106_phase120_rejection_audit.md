# V99 R106 Phase120 — rejection/failure-mechanism audit

Decision: **PERMANENT SCIENTIFIC REJECT**. No retuning, sign flip, universe substitution, cost relaxation, or holdout inspection.

The preregistered train-only severe-cost result is unambiguously destructive: ROI -99.3784%, PF 0.15776, max drawdown 99.3785%, positive-hour ratio 18.30%, robust mean after removing the top 1% remains negative (-2.8878e-4/hour), and 0/4 chronological folds are healthy. All four eligible folds lose roughly 71.6%–72.7% with PF 0.121–0.224. This is therefore not a tail-concentration accident and not a single temporal-regime failure; the failure is broad and persistent across the entire train chronology.

Causal/data discipline remained intact in the recorded evidence: all alpha was t-1, selection was train-only, holdout was not parsed, missing archives were not filled, and V16/V99 Frozen were untouched. Consequently the correct scientific action is rejection, not repair of Phase120.

Mechanism inference allowed by the evidence: all-trade hourly taker-quantity continuation does not survive the canonical severe execution model in this cross-sectional construction. Because robust mean excluding the best 1% is still materially negative and every fold fails, chasing rare winners or changing the sign after observing PnL would be classic post-hoc overfit and is prohibited.

Phase121 remains scientifically distinct because it conditions on causally unusual trade size rather than retuning Phase120. However its exact rolling individual-trade quantile requirement must be implemented without approximation; if exact implementation is operationally infeasible under the available runner budget, Phase121 must be rejected operationally rather than silently changing its preregistration.
