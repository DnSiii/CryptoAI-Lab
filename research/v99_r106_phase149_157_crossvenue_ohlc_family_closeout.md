# V99 R106 — Phase149–157 cross-venue OHLC family closeout

## Decision
The direct cross-venue OHLC-geometry reversion family is CLOSED after Phase157. Do not rescue it with post-hoc sign flips, threshold grids, alternate lookbacks, or selective asset removal.

## Evidence basis
The repository contains permanent TRAIN-gate reports for Phase149 through Phase157. Phase157 itself ended `TRAIN_ALPHA_REJECT` with 0/4 healthy temporal folds, ROI -0.9949026354, profit factor 0.2078286122, max drawdown 0.9949025343, positive-hour ratio 0.1857302742, and robust mean without top 1% -0.0003246251 per hour. Its aligned data coverage remained above the preregistered 98% gate and all Phase136 hashes/causal invariants passed.

The earlier members of the family likewise failed their preregistered TRAIN gates. This pattern is sufficient to stop spending research budget on cosmetic transforms of the same OHLC cross-venue disagreement mechanism.

## Failure-mechanism interpretation
The negative result is not explained by one missing-data incident or one temporal fold. Phase157 had four valid folds and zero healthy folds, while source-integrity and causality checks passed. The family therefore lacks evidence of robust net positive expectancy under the severe-cost execution model used by V99 R106.

## Next scientific direction
Move to orthogonal microstructure information rather than another OHLC transform. Phase158 is preregistered as a DATA-ONLY cross-venue perpetual-funding divergence audit. No PnL or alpha direction is allowed until the funding source passes deterministic coverage/alignment/integrity gates and a later hypothesis is separately preregistered.

## Governance
- V16 Frozen untouched.
- V99 Frozen untouched.
- Holdout remains untouched.
- No sign flip or rescue of Phase149–157.
- No parameter tuning based on failed PnL.
