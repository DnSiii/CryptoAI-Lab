# V98 Independent — Phase191 failure audit

Status: **REJECT_FAMILY_NO_RESCUE**.

Scope is training-only (2023-01-01 through 2025-12-31). Validation and final holdout remain closed. V16/V99 are not used for selection.

## Evidence

All eight preregistered low-volatility cross-sectional trend specifications failed the frozen gate. There is no winner.

The family exhibits a recurring chronological pathology: 2024 can look profitable while 2023 and/or 2025 are negative. Examples from the harvested report:

- `w336_q35_h24`: 2023 -12.75% / PF 0.877; 2024 +37.33% / PF 1.399; 2025 -26.30% / PF 0.696.
- `w720_q35_h24`: 2023 -8.28% / PF 0.921; 2024 +20.47% / PF 1.227; 2025 -23.53% / PF 0.718.
- `w720_q50_h24`: 2023 -4.40% / PF 0.986; 2024 +20.18% / PF 1.168; 2025 -20.33% / PF 0.825.

Cost stress confirms the apparent 2024 edge is not economically robust. For `w720_q50_h24`, aggregate base return is -8.67% / PF 0.996 / MDD -31.86%; severe is -39.93% / PF 0.878 / MDD -49.23%; supersevere is -69.07% / PF 0.722 / MDD -73.72%.

Regime behavior is also unstable. `w720_q50_h24` has positive approximate contribution in bear and bull but materially negative sideways contribution; other family members commonly show the same sideways weakness. This is not a broad regime-independent edge.

The rejection is not driven by a single tail statistic: reported top/bottom-10 shares are generally well below 50%. Position concentration is structurally 50% top-1 because the construction holds one long and one short, so the decisive failures are economic edge, chronological consistency, drawdown/risk invariants and stress robustness rather than a hidden tail-only artifact.

## Integrity / reproducibility

The workflow rebuilt canonical data with cutoff 2025-12, asserted every canonical timestamp is before 2026-01-01, ran Phase191 twice, and obtained byte-identical SHA-256 `3b8a2cee2c4ed49ea450a6b4264067f90132e5036f365f73f417f8b657b21749`.

The harvested report records `training_only=true`, `validation=null`, `final_holdout=null`, `v16_used=false`, and `v99_used=false`.

## Decision

Reject the entire Phase191 family with **no rescue, inversion, threshold adjustment, or validation peek**. The next hypothesis must be scientifically distinct and preregistered before execution.
