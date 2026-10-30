# V98 Independent — Phase155 failure audit

Date: 2026-09-26
Scope: training-only evidence from Phase155. Validation and final holdout remain unopened.

## Decision
REJECT_NO_RESCUE remains binding.

## Independent findings
- Aggregate total return: -24.5033%; daily PF: 0.8191; max drawdown: -31.7014%.
- Chronological folds do not replicate: 2023 -26.0320% / PF 0.6882; 2024 +2.0666% / PF 1.0504; 2025 had zero exposure because the preregistered inversion condition was absent in the available macro observations.
- Friction sensitivity is adverse rather than robust: severe -27.4270% / PF 0.7952; supersevere -31.6119% / PF 0.7609.
- Regime attribution is negative in bear, bull, and sideways regimes. This is broad mechanism failure rather than one isolated market regime.
- Tail concentration is material but not a valid rescue: bottom-10 negative days account for 19.0680% of negative-day loss; worst day -6.3934%; CVaR5 -1.4614%.
- No asset generated positive aggregate contribution under the frozen accounting. Removing assets, flipping the sign, changing the inversion threshold, changing lag, or selecting only 2024 would be post-hoc rescue and is prohibited.
- Reproducibility/invariants passed in workflow run 36252770126: deterministic report replay, Phase154 data-only dependency hash verification, closed validation/final holdout, no parameter search, no V16/V99 use.

## Scientific interpretation
The simple hypothesis that an already-observed negative 10Y-2Y Treasury spread is a causal next-day risk-off short signal for the crypto basket is falsified on the training folds. The loss occurs across regimes and worsens under stronger friction assumptions, while temporal replication is absent. The family is therefore closed without rescue.

## Next-family constraint
The next experiment must be orthogonal to the rejected yield-curve-level family and must begin DATA_ONLY. Do not use sign inversion, threshold sweeps, alternate moving averages, asset deletion, or exposure retuning as a continuation of Phase155.
