# V98 Independent Phase190 — family independence / anti-overfit audit

Decision: **INDEPENDENT_ENOUGH_TO_TEST, TRAINING ONLY**.

## Prior failure mechanism carried forward
Phase189's nearest specification had +3.8934% aggregate base return but negative 2024/2025 folds, severe -2.6372%, supersevere -12.2122%, and positive attribution only in sideways. Tails and concentration were not the main pathology. Therefore Phase190 is not allowed to change Phase189 windows/quantiles/holding period, invert its mean-reversion sign, remove losing regimes/assets, or otherwise rescue that family.

## Orthogonality check
Phase190 uses a time-series asset-level state (`rv24 / rolling median(rv24)`) intersected with absolute directional displacement. It does not rank cross-sectional dispersion and does not select winners/losers relative to peers. The economic hypothesis is post-shock continuation after information arrival, not cross-sectional convergence after dispersion.

Related historical V98 families were reviewed conceptually for collision: generic volatility compression, volatility-of-volatility, realized-volatility regime, jump-breadth/rebound, and idiosyncratic momentum. Phase190 is admissible only because its frozen interaction, trigger and trade direction are materially different; it must not be interpreted as permission to reopen those closed families.

## Anti-overfit boundaries
- exactly 8 preregistered specifications;
- one fixed displacement threshold;
- no asset exclusions;
- no regime permission filter;
- no post-result sign inversion;
- no cost relaxation;
- no validation peek;
- no final-holdout peek;
- no V99 evidence for selection;
- failure of fold or stress gates closes the entire exact family.

## Audit conclusion
Proceed to deterministic implementation and training-only execution. Any implementation ambiguity must be resolved in the conservative/causal direction and documented before economic results are accepted. Validation remains closed.