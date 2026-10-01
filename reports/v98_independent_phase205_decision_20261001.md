# V98 Independent — Phase205 decision

Date: 2026-10-01
Branch: `research/v98-independent-zero`
Scope: V98 Independent only.

## Decision

**REJECT_FAMILY_NO_RESCUE** — BTC→alt lead/lag underreaction is not promoted.

## Evidence harvested

The deterministic workflow completed successfully after rebuilding the training-only archive and enforcing the `<2026-01-01` firewall. Two independent evaluator executions produced the same report hash (`ed33a0a663984a8bfd99058618ac4ef795f66f4964ccf7a780a11490c42cba04`). The report itself records deterministic payload SHA256 `97af66f6db25ffe8ff4721c2b96a4c534741477a0bf29d4657e69352313c2180`.

The family does not show fold-stable net edge after realistic costs. Example preregistered spec `w3_z1p5_h3`: 2023 base return -8.60%, PF 0.867, MDD -11.48%; 2024 base return -1.20%, PF 0.993, MDD -10.38%. Cost stress deteriorates the same mechanism materially: in 2023 severe PF 0.703 / return -20.43%, supersevere PF 0.488 / return -39.71%; in 2024 severe PF 0.837 / return -15.81%, supersevere PF 0.617 / return -38.87%. This is not a cost-only failure: base economics are already non-robust.

Regime evidence is inconsistent rather than a durable causal edge. The same representative spec has isolated positive pockets (e.g. 2023 bear PF 1.45 and 2024 bull PF 1.13 at base costs) while the complementary regimes are sub-1 PF and aggregate folds fail. These pockets are not grounds for a post-hoc regime filter.

Concentration is not the sole explanation: the representative spec's max asset concentration is ~37.6% in 2023 and ~29.4% in 2024 while aggregate performance is still negative. Asset signs also rotate (ETH positive in 2023; XRP positive in 2024), arguing against a stable responder-specific mechanism.

Trade-level tails are now measured on complete trade PnL (entry, holding/funding, exit), fixing the Phase204 diagnostic weakness. Median trade PnL is negative in the inspected fold/spec and severe/supersevere shift the distribution downward, so there is no hidden positive median being obscured by a few catastrophic trades.

## Data/integrity audit

Training data were rebuilt from source. BTC and ETH contain 52,608 hourly rows through 2025-12-31 23:00 UTC with zero missing hours. BNB starts 2020-02-10 and has zero missing hours. XRP and SOL each report a 120-hour gap beginning 2022-02-26; because Phase205 evaluation folds are 2023/2024/2025, this historical gap is outside the evaluated folds but remains documented and must not be silently imputed for experiments using 2022 or earlier. All evaluated canonical indices passed monotonicity, duplicate, universe, and `<2026` holdout-leak invariants.

## Anti-overfit ruling

No rescue, inversion, responder cherry-pick, regime filter, threshold retuning, or holdout inspection is permitted from this result. Validation/final holdout remain unopened. V16 Frozen, V99 Frozen, V99 research/workflows/reports/paper state remain untouched.

## Next

Proceed only to a scientifically distinct preregistered family. Phase206 is preregistered separately before implementation/results.