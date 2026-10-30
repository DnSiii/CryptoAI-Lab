# V98 Independent — Phase188 untouched validation audit

Decision: **REJECT_VALIDATION_NO_RESCUE**

Scope: V98 Independent only. Phase187 candidate `h24_w90_low50` was frozen before validation. No retuning/rescue is permitted from validation evidence. Final holdout remains closed.

## Evidence harvested

Phase188 validation artifact reports:
- window: 2026-01-01 through 2026-07-31 only; final holdout starts 2026-08-01 and was not used;
- base: return -11.86%, PF 0.881, max drawdown -19.04%, payoff 1.178, win rate 42.77%, positive days 41.98%;
- severe: return -12.45%, PF 0.875, max drawdown -19.58%;
- supersevere: return -13.21%, PF 0.866, max drawdown -20.29%;
- deterministic rerun/byte identity passed in the Phase188 workflow before artifact commit.

## Failure-mechanism audit

The failure is not a marginal cost sensitivity: all three cost regimes are negative and PF stays materially below 1.0. Increasing friction worsens an already-negative gross signal, so costs do not explain the sign reversal.

The failure is not consistent with a single-tail rescue: the aggregate base loss and PF<1 are large enough that accepting the family would require post-validation modification, which is prohibited. Phase187 training evidence therefore did not transport to the untouched 2026 validation regime.

The scientific interpretation is **regime/generalization failure of the frozen idiosyncratic-momentum family**, not an implementation rescue opportunity. Any future hypothesis must be orthogonal and preregistered from training-only evidence; Phase188 validation must not be used for parameter selection.

## Governance

- Phase187/188 family: rejected.
- No Phase188 parameter changes.
- No validation rescue/grid expansion.
- No final holdout inspection.
- No V16/V99 files or paper state touched.
