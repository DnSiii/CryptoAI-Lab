# V99 R106 Phase194A — operator freeze before first economic trial

Status: **PREREGISTERED AMENDMENT / TRAIN_ONLY / economic_trials=0**

This amendment resolves the only material ambiguity found in Phase194 before any PnL is inspected. Phase194 said "additive/veto candidate" but did not freeze which operator would be tested. Testing both and selecting after results would create an unregistered multiplicity degree of freedom, so only one operator is admitted.

## Frozen operator

- **Operator:** additive overlay only. The veto alternative is not tested in H194 and is permanently excluded from this trial.
- **Direction:** positive causal USDC net-issuer z-sign is risk-on; negative sign is risk-off. This sign is fixed ex ante and must not be flipped after results.
- **Instrument mapping:** equal BTCUSDT and ETHUSDT directional overlay, +0.05 each when sign=+1 and -0.05 each when sign=-1; overlay gross = 0.10.
- **Integration:** add the overlay to the already-frozen R106 baseline targets, then apply the existing portfolio gross cap. The baseline engine, router, sleeves, side-aware controller and benchmark construction may not be refit or altered because of H194.
- **Timing:** decision bar t may use only the newest 24h UTC source bucket with bucket_end < t. Same-bar equality is ineligible.
- **Normalization:** expanding TRAIN-only history strictly preceding the eligible bucket; no full-sample statistics and no magnitude threshold.
- **Holding/update:** overlay sign is carried until the next causally eligible completed 24h bucket; no intraday refresh from partial buckets.
- **Costs:** charge turnover under the existing canonical severe and supersevere per-side cost definitions.
- **No sweep:** no alternative overlay gross, BTC/ETH weights, sign, clock, horizon, threshold, veto, or baseline modification may be tested inside H194 after economic results are seen.

## Evaluation order

1. causality/mutation invariant;
2. deterministic byte-identical rebuild;
3. chronological TRAIN evaluation and temporal folds;
4. severe then supersevere cost survival;
5. full BULL/BEAR/SIDEWAYS x HIGH/LOW volatility matrix using causal prior-known regimes;
6. benchmark-envelope comparison;
7. tails/concentration and remove-best-period attribution;
8. reject if any mandatory TRAIN gate fails; untouched holdout remains unopened until all TRAIN gates pass.

V16 Frozen and V99 Frozen remain read-only. This amendment is a design freeze, not evidence of alpha.
