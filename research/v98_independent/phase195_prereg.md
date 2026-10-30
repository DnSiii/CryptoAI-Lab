# V98 Independent — Phase195 preregistration

Status: FROZEN BEFORE EXECUTION

## Hypothesis
Cross-sectional liquidity-adjusted trend persistence: among sufficiently liquid assets, rank a causal trailing return signal normalized by trailing quote-volume participation. The hypothesis is scientifically distinct from Phase194 abnormal-volume reversal: Phase195 tests persistent relative trend conditioned on stable liquidity rather than reversal after a volume shock.

## Information set / causality
- Training only: 2023-01-01 through 2025-12-31.
- No validation or final-holdout observations may be read, summarized, parameterized, or used for selection.
- At decision hour t, all signal inputs must end at t-1.
- Universe/liquidity eligibility must be computed from trailing information only.
- No V99/V16 state, reports, parameters, workflows, or paper state may be consulted.

## Frozen grid (8 specifications)
Cartesian product:
- trend lookback: 24h, 72h
- liquidity lookback: 24h, 168h
- holding horizon: 6h, 12h

Signal: trailing log return / sqrt(max(trailing quote-volume share, epsilon)); rank cross-sectionally after liquidity eligibility. Long top-ranked and short bottom-ranked eligible asset with equal gross legs; no rescue/inversion after observing results.

Liquidity eligibility: asset trailing quote volume must be >= cross-sectional median at t-1. Quote-volume share denominator uses only eligible contemporaneous trailing quote volume available at t-1.

## Evaluation contract
Chronological folds: calendar 2023, 2024, 2025 plus aggregate training period. Report total return/CAGR, max drawdown, daily Profit Factor, payoff, win rate, positive/negative days, turnover, gross/net exposure, best/worst day, p01/p05/CVaR, regimes, top-1 concentration and tail contribution.

Run realistic base costs/funding plus severe and supersevere cost scenarios using the repository's existing V98 Independent economic-cost conventions. Funding must remain causal and asset-specific where available.

## Gates
A specification may advance only if aggregate edge is positive after base costs, chronological folds are not dependent on one isolated year, drawdown is acceptable under the existing V98 Independent gate convention, severe/supersevere stress does not destroy the economic thesis, concentration/tails are not pathological, exposure invariants pass, and deterministic reruns are byte-identical.

Failure means REJECT_FAMILY_NO_RESCUE. Do not tune this frozen grid after results. A pass may only advance to the next pre-existing validation gate; final holdout remains untouched until a formally frozen candidate reaches it under project discipline.
