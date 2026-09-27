# V99 R106 Phase161 — Cross-Asset Funding-Acceleration Dispersion

## Status
PREREGISTERED AFTER Phase160 permanent TRAIN rejection and BEFORE ANY Phase161 PnL. TRAIN-only. Scientifically distinct second-difference hypothesis; it does not rescue, tune, or reinterpret Phase159/160.

## Scientific hypothesis
Funding level and first change both failed. Test whether *acceleration* of positioning flow contains distinct information: a sudden acceleration in an asset's funding change relative to peers may represent short-lived crowding that subsequently mean-reverts. Test REVERSION only. No sign flip after results.

## Frozen feature
Universe BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT. Binance Vision deterministic monthly fundingRate archives only. At native event t for asset i compute delta_i(t)=funding_i(t)-funding_i(previous event) and accel_i(t)=delta_i(t)-delta_i(previous event), using only strictly prior native observations. At a cross-sectional event require >=4/5 current accelerations with current timestamps no more than 60 minutes old; never nearest-future matching. Define x_i(t)=accel_i(t)-median_j(accel_j(t)). Normalize each asset with trailing 168 valid x observations shifted by one event: z_i(t)=(x_i(t)-median_168[x_i(<t)])/(1.4826*MAD_168[x_i(<t)]). Direction is REVERSION only: weight proportional to -z, cross-sectionally normalized, portfolio L1<=1. State at t executes only from the next hourly bar, exact 1h lag.

## Frozen data/gates
TRAIN 2021-12-01 inclusive to 2024-01-18 exclusive. No holdout fetch/use for construction, normalization, selection, diagnostics, thresholds, or decisions. Same Phase159 deterministic source/data contract and >=95% per-asset / >=90% cross-sectional coverage gates. No asset deletion, threshold sweep, alternate lookback, winsorization, sign rescue, parameter tuning, or post-PnL mutation.

## Validation discipline
Chronological TRAIN-only decision; four temporal folds; causal assertions; untouched holdout; severe and supersevere cost gates; regime matrix; tails/concentration audit; benchmark envelope; deterministic rerun/reproducibility. Downstream gates only if base TRAIN gate passes.

## Decision rule
Any integrity/coverage/causality failure => DATA/INTEGRITY REJECT. Base TRAIN failure => permanent scientific REJECT, no tuning/sign flip. Base PASS => freeze implementation and immediately continue through all downstream gates before promotion. V16 Frozen and V99 Frozen are immutable.
