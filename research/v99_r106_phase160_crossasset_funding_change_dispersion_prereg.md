# V99 R106 Phase160 — Cross-Asset Funding-Change Dispersion

## Status
PREREGISTERED BEFORE ANY Phase160 PnL. TRAIN-only. This is a scientifically distinct dynamic hypothesis prepared while Phase159 level-dispersion evaluation runs; it does not depend on the Phase159 PnL sign or permit rescue/tuning of Phase159.

## Scientific hypothesis
The *change* in perpetual funding contains positioning-flow information distinct from the funding level. When an asset's causal funding-rate change is unusually positive/negative relative to contemporaneous cross-asset funding changes, the abrupt positioning imbalance may mean-revert in subsequent returns. Test REVERSION only. No sign flip after results.

## Frozen feature
Universe BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT. Binance Vision deterministic monthly fundingRate archives only. At native funding event t, for asset i compute delta_i(t)=funding_i(t)-funding_i(previous native funding event strictly before t). Require current and previous observations to be causal and TRAIN-contained. At a cross-sectional event require >=4/5 current deltas available with current funding timestamps no more than 60 minutes old; never nearest-future matching. Define x_i(t)=delta_i(t)-median_j(delta_j(t)). Normalize each asset with its own trailing 168 valid x observations, history shifted by one event: z_i(t)=(x_i(t)-median_168[x_i(<t)])/(1.4826*MAD_168[x_i(<t)]). Direction=-sign(z), continuous bounded cross-sectional magnitude using the same Phase159/Phase136-compatible allocator, portfolio L1<=1. Funding state at t may execute only from the next hourly bar (exact 1h execution lag after state construction).

## Frozen data/gates
TRAIN 2021-12-01 inclusive to 2024-01-18 exclusive. No holdout fetch/use for feature construction, normalization, selection, diagnostics, thresholds, or decisions. Per-asset source coverage >=95%, finite/strictly increasing/TRAIN-contained timestamps; cross-sectional event coverage >=90%. No asset deletion, threshold sweep, alternate lookback, winsorization, sign rescue, parameter tuning, or post-PnL feature mutation.

## Validation discipline
Chronological TRAIN-only decision; four temporal folds; causal assertions; untouched holdout; severe and supersevere cost gates; regime matrix; tails/concentration audit; benchmark envelope; deterministic rerun/reproducibility. Downstream gates only if base TRAIN gate passes.

## Decision rule
Any integrity/coverage/causality failure => DATA/INTEGRITY REJECT. Base TRAIN failure => scientific REJECT permanently, no tuning/sign flip. Base PASS => freeze implementation and continue immediately through all downstream gates before promotion. V16 Frozen and V99 Frozen are immutable.
