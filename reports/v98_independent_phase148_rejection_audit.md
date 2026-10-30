# V98 Independent — Phase148 rejection audit

Decision: **REJECT_NO_RESCUE**.

## Evidence

Phase148 completed deterministic training-only replay after Phase147 PASS_DATA_ONLY. Aggregate return was -27.9511%, daily Profit Factor 0.83058 and max drawdown -38.4806%. Every chronological annual fold failed independently: 2023 -5.2938% / PF 0.88997; 2024 -21.9950% / PF 0.72167; 2025 -2.1954% / PF 0.98263. Severe and supersevere costs remained negative (-29.4246% and -31.4293%).

## Failure mechanism

This is not a marginal cost failure. Base expectancy is negative and deterioration under higher costs is monotonic. The weakness is temporally broad rather than one-fold concentration. Bull hours contributed approximately -0.3423 while sideways was only approximately +0.0388 and bear approximately -0.0020; the preregistered broad-dollar-up => crypto-short mapping therefore does not generalize as a risk-off edge in this training window.

Tail concentration does not rescue the candidate: top-10 positive-day share was 17.77%, while p01 was -2.2041%, CVaR05 -1.6773%, worst day -5.1043%. Mean top-1 weight share was 22.27% (p95 27.66%), so failure is not attributable to a single-asset concentration accident.

## Governance

No sign flip, threshold search, alternate lookback, regime carve-out, asset deletion, or sizing rescue is permitted for Phase148. Validation and final holdout remain unopened/null. V16 and V99 are not used. Champion remains none.

Next research must use a scientifically distinct data family and begin DATA_ONLY before any crypto-return relationship is inspected.