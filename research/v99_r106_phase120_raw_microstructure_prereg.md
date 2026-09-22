# V99 R106 Phase120 — raw aggTrades taker-imbalance persistence TRAIN-ONLY preregistration

Phase120 is preregistered while Phase119 is pending and MUST NOT run unless Phase119 records `INTEGRITY_PROBE_PASS`. No Phase119 market-value distributions or return relationships may be used to alter this specification.

## Scientific distinction
Recent Phases100–111 used already-aggregated Binance derivatives metrics (hourly taker ratios, OI, top-trader ratios). Phase120 instead uses raw official USD-M `aggTrades`, reconstructing signed aggressive notional from buyer-maker flags. This tests whether within-hour execution pressure has persistence after severe costs rather than reparameterizing the failed aggregate-ratio family.

## Frozen hypothesis
For each symbol/hour t, compute signed aggressive notional `sum(price*qty*(+1 if buyer_is_maker=false else -1))` divided by total aggressive notional. Require nonzero total notional. Cross-sectionally median-center this imbalance at t, divide by cross-sectional MAD with deterministic epsilon guard, clip robust z to [-4,4], then apply tanh(z). The complete signal is shifted exactly one hour before exposure: weights at t use feature t-1 only. L1-normalize across available canonical symbols, fixed gross exposure 0.20.

Direction is **continuation/persistence**: relatively buyer-aggressive symbols long, relatively seller-aggressive symbols short. No sign flip is permitted after seeing PnL.

## Data and temporal discipline
- Canonical PIT48 universe only; quarantines already mandated by repository integrity rules remain excluded where applicable.
- Official Binance USD-M daily `aggTrades` archives only.
- Train ends exclusively at 2024-01-18T00:00:00Z. Holdout archives/content are prohibited at this gate.
- Missing archives/hours are not forward-filled or synthesized.
- Feature hour must be complete before it can become t-1 input.
- Existing four chronological folds are unchanged.

## Fixed evaluation gate
Single hypothesis, no grid/search. Use the repository's existing severe-cost accounting and train stability requirements. A train pass requires positive aggregate ROI/PF>1 after severe costs, valid chronological fold support with the established healthy-fold requirement, and positive robust mean after removing top 1% contributions. Failure is permanent for this exact hypothesis; no threshold search, horizon search, selective symbols, sign flip, or cost relaxation.

Only after a train pass may the exact frozen candidate proceed to supersevere costs, regime matrix, benchmark envelope and reproducibility gates. Untouched holdout remains sealed until all prior gates pass.

V16 Frozen and V99 Frozen remain immutable.
