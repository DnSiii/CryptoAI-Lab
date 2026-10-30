# V98 Independent — Phase193 training audit

**Decision: REJECT_FAMILY_NO_RESCUE. TRAINING ONLY.**

Validation remains untouched; final holdout remains closed. V16/V99 were not used.

## Evidence harvested

The deterministic Phase193 workflow completed successfully and rebuilt canonical data with a strict `< 2026-01-01` boundary for both prices and funding. Two complete executions produced the identical report SHA256 `77a6623be84402490804a7e1cca220cec718b4ae6e98d815161ed322e8b91d14`.

All economically active specifications failed the preregistered edge, drawdown, chronological-fold and stress gates. The least-bad aggregate base result was `f72_h24_g50`: total return -5.90%, PF 1.008, MDD -48.95%; severe -25.73% / PF 0.934 / MDD -55.90%; supersevere -47.77% / PF 0.835 / MDD -65.73%.

The apparent 2023 strength is not stable: `f72_h24_g50` produced +68.96% / PF 1.635 in 2023, then -17.47% / PF 0.877 in 2024 and -32.72% / PF 0.663 in 2025. `f72_h12_g50` similarly moved from +50.39% / PF 1.434 in 2023 to -42.41% / PF 0.615 in 2024 and -30.06% / PF 0.707 in 2025. This is structural chronological decay, not a marginal cost issue.

Regime evidence also rejects broad carry: bear was positive in several variants while bull was materially negative; the family lacks breadth. Tail shares are moderate (roughly 11–21% in active variants), so a handful of outliers does not explain the failure. Position concentration is mechanically 50% top-1 because the frozen construction holds one long and one short; it stays within the preregistered 60% limit.

## Integrity anomaly

`f72_h24_g0` emitted zero active days / NaN economics and failed `risk_invariant`. It is treated as an invalid specification, never as evidence for promotion. The family decision does not depend on it: the other seven economically active specifications independently fail the required gates. No post-result repair or rerun is allowed as a Phase193 rescue.

## Scientific conclusion

The lagged cross-sectional funding-carry hypothesis is rejected for this V98 universe and training period. Funding carry displayed a transient 2023 effect that reversed in 2024–2025 and deteriorated further under severe/supersevere economics. Do not tune lookbacks, flip signs, add price filters, or open validation for this family.
