# V99 R106 — Phase182 TRAIN rejection

Date: 2026-09-29
Status: PERMANENT REJECT / NO RETUNE / NO HOLDOUT

## Evidence harvested

GitHub Actions run 36634144212 completed successfully on commit 103b7d36. All 11 integrity/feature/evaluator invariants passed. The frozen TRAIN evaluator was executed twice and the emitted JSON was byte-identical. V16 Frozen and V99 Frozen hashes were unchanged. The evaluator explicitly reports `holdout_market_values_parsed=false`.

The frozen Phase182 mapping fails decisively before any regime/benchmark or holdout gate is needed:

- Severe cost 0.0007/side: total return -38.5789%, max drawdown -38.9243%, healthy folds 0/5.
- Severe fold returns: -10.5753%, -9.0248%, -8.9639%, -9.3933%, -8.4701%.
- Supersevere cost 0.0014/side: total return -60.5987%, max drawdown -60.6576%, healthy folds 0/5.
- Supersevere fold returns: -18.2349%, -18.0097%, -15.9639%, -16.2006%, -16.5410%.
- Remove-best-hour remains negative: -38.9886% severe and -60.8614% supersevere.

This is broad chronological failure, not a single-fold or single-tail pathology. Costs worsen an already unacceptable mapping and every fold is negative under both required cost levels. There is therefore no scientific basis to spend a holdout query or to tune signs, windows, weights, thresholds, gross, normalization, or feature membership.

## Decision

Phase182 is permanently rejected exactly as preregistered. Do not retune or resurrect this mapping. Holdout remains untouched. V16 Frozen and V99 Frozen remain immutable.

The next experiment must be scientifically distinct and preregistered before any PnL inspection.
