# V99 R106 Phase121 — causal large-trade pressure (preregistered)

Status: **PREREGISTERED ONLY — DO NOT RUN UNTIL PHASE120 IS HARVESTED/DECIDED**.

## Scientific question
Does the imbalance carried specifically by unusually large aggressive trades contain train-only cross-sectional information distinct from Phase120's all-trade quantity imbalance?

## Frozen hypothesis before any alpha result
- Source: official Binance USD-M `aggTrades` archives already provenance/integrity-gated by Phases118–119.
- Evaluation window: canonical train only, ending **2024-01-18 00:00:00 UTC exclusive**. No holdout market values may be downloaded, parsed, inspected, summarized, or used for selection.
- Tradable universe must be the intersection of the precommitted Phase118 resource universe and the canonical executable V15 universe; membership is fixed before return/PnL evaluation. If the precommitted resource rule cannot supply at least 8 executable assets, reject operationally rather than substitute assets after seeing performance.
- Per asset/hour, aggregate aggressive buy and sell quantity only for trades whose quantity exceeds that asset's causal trailing 30-day (720 hourly observations) 90th percentile of individual-trade quantity. The threshold at hour t must be computed solely from trades timestamped strictly before hour t; current-hour trades cannot set their own threshold.
- Raw feature: `(large_aggressive_buy_qty - large_aggressive_sell_qty) / (large_aggressive_buy_qty + large_aggressive_sell_qty)` when denominator > 0; otherwise missing.
- Cross-section: median/MAD robust z-score using at least 8 available assets; transform with `tanh`.
- Direction: continuation, frozen now. No sign flip.
- Entire signal is shifted by one complete hourly bar before target construction (causal t-1).
- Portfolio: cross-sectional L1 normalization; gross alpha budget 0.20, identical execution/guardrails to the canonical R106 harness.
- Missing archives/hours remain missing. No backfill from future observations and no synthetic imputation.

## Selection / anti-overfit rules
Single hypothesis only. No grid over percentile, lookback, horizon, transform, sign, universe, or gross. The 90th percentile, 30-day trailing window, continuation sign, tanh transform, t-1 lag, and 0.20 gross are frozen before evaluation. No parameter may be changed because of Phase121 PnL.

## Gate sequence
1. Causality/data-integrity assertions and executable-universe invariant.
2. Train-only severe-cost alpha gate with chronological temporal folds.
3. If and only if train gate passes, freeze exact specification and run supersevere costs.
4. Then regime matrix and concentration/tail/pathology audit.
5. Then benchmark envelope and deterministic reproducibility/invariant rerun.
6. Untouched holdout remains prohibited until every preceding gate passes with the exact frozen specification.

A failure at any scientific gate permanently rejects this exact Phase121 hypothesis; do not retune it. Infrastructure failures may be repaired without changing the preregistered hypothesis.

## Independence rationale
Phase120 asks whether aggregate taker quantity imbalance across all trades is predictive. Phase121 isolates the pressure of causally-defined unusually large trades. This changes the economic mechanism being tested (size-conditioned informed/aggressive flow) rather than merely tuning Phase120's transform or sign.
