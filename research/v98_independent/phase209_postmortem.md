# V98 Independent — Phase209 independent postmortem

## Mechanical status
**REJECT_FAMILY_NO_RESCUE.** Phase209 was preregistered as an 8-spec closed family. No parameter expansion, inversion, asset removal, regime filter, or rescue is permitted after observing results.

## Failure mechanism
The first frozen spec (`disp30d_q900_hold12h`) is already decisively uneconomic at base cost in 2023: return -71.05%, PF 0.845, MDD -72.21%, positive-day fraction 35.34%, with 351 trades. Severe and supersevere worsen economics. Asset contributions are negative across BNB, ETH, SOL and XRP; SOL is largest but the sign is not a single-asset artifact. Bull, bear and sideways decompositions are all negative in 2023, so a regime carve-out would be post-hoc selection rather than a causal rescue.

The result therefore supports a structural interpretation: extreme one-hour cross-sectional dispersion in this universe is not a robust temporary-liquidity mean-reversion signal after realistic turnover/funding. The family should not be inverted either; doing so after observing failure would convert a falsified preregistration into data-mining.

## Integrity / anti-overfit decision
- Keep chronological 2023/2024/2025 folds separate.
- Do not inspect validation/final holdout.
- Do not use V99 state, reports or results for V98 selection.
- Preserve base/severe/supersevere costs, realized funding, regimes, tails and concentration diagnostics.
- Do not reuse Phase209 pockets (specific asset/regime/threshold/holding period) as a new candidate.

## Next scientific direction
Move to Phase210, preregistered before any Phase210 result, using **asset-specific hour-of-week residual surprise**. This introduces a distinct information family: recurring intraday microstructure/flow seasonality. It does not condition on funding level, BTC residual momentum, volatility compression, or contemporaneous cross-sectional dispersion.
