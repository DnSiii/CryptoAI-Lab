# V98 Independent Phase174 — Phase172 validation failure audit

Decision: **REJECT_VALIDATION_NO_RESCUE**.

Scope: V98 Independent only. V16/V99 are not used. Final holdout remains unopened.

## Frozen evidence

Training candidate: `phase172_t10y2y_steepening_long` / blob `03a3baef73ab940e6a503a604cb17287e095f337`.
Validation evidence: `reports/v98_independent_phase173_validation.json`.
Validation window: 2026-01-01 through 2026-07-31. Final holdout is null.

## Independent failure audit

The validation failure is broad, not a single-asset or single-regime accident:

- base total return = -10.9789%; PF = 0.7956; payoff = 0.8665; win rate = 47.87%; positive days = 101/211; max drawdown = -16.13%; ruin=false.
- severe total return = -11.1424%; PF = 0.7927; max drawdown = -16.24%.
- supersevere total return = -11.3936%; PF = 0.7882; max drawdown = -16.41%.
- all five asset contribution shares are negative: BTC -14.91%, ETH -19.86%, BNB -18.02%, XRP -24.48%, SOL -22.73% of the negative aggregate contribution.
- regime return sums are negative in bear (-2.84%), bull (-0.29%), and sideways (-7.54%). Sideways is the largest damage bucket, but no regime rescues the hypothesis.
- tails are materially concentrated (bottom-10 negative-day share 31.13%; top-10 positive-day share 33.58%) but the rejection does not depend on a few tail days because PF<1 and aggregate return is negative.
- concentration is not pathological: mean active assets 5.0, mean top-1 weight share 22.07%, p95 23.27%, max gross 32.72% < 35% cap.

## Training-to-validation break

Training 2023-2025 was +48.54%, PF 1.2959, MDD -11.14%, with every annual fold positive, but edge decayed monotonically: 2023 +30.90% / PF 1.7701; 2024 +9.68% / PF 1.1844; 2025 +3.33% / PF 1.0609. Validation then crossed below zero to -10.98% / PF 0.7956. This is consistent with temporal edge decay / regime nonstationarity rather than a validation implementation artifact.

## Scientific decision

Reject the T10Y2Y steepening-long hypothesis. No inversion, threshold search, lookback search, asset pruning, regime filtering, exposure reduction, or validation-informed rescue is allowed. Do not open final holdout for this candidate.

Next research must be a scientifically distinct, independently preregistered data family/hypothesis, with training-only selection and the same chronological/causal/cost/reproducibility discipline.
