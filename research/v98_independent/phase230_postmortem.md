# V98 Independent Phase230 — decision-grade post-mortem

Status: REJECT_FAMILY_NO_RESCUE. Phase230 is closed; no parameter rescue is permitted.

## Reproducibility / integrity
- Decision-grade workflow completed successfully from branch `research/v98-independent-zero`.
- Training-only rebuild ends before 2026-01-01; holdout 2026+ remained unopened.
- Point-in-time funding and causal signal invariant passed: decision at `open(t)` uses residual returns ending no later than `open(t-1)`.
- Two evaluator runs were byte-identical.
- Deterministic payload SHA256: `6f83cb1ceb8e1659c91908467d687d5b7fcb2af256a1f2a81d7d8944b89dd8b5`.
- Mechanical validator returned zero survivors and `REJECT_FAMILY_NO_RESCUE`.

## Failure mechanism audit
The family shows a tempting but non-stationary 2023 edge that does not survive chronology. Example frozen spec `idio_mom_lb168_k1_h4`: base return +87.62%, PF 1.066 and DD -19.67% in 2023, then +11.12%, PF 1.016 and DD -46.20% in 2024, then -33.33%, PF 0.963 and DD -41.63% in 2025. This is exactly the pattern the chronological gate is intended to reject.

The apparent early edge is concentrated. For that 2023 fold, SOL contributes about +1.038 while BNB, ETH and XRP are negative; reported max asset concentration is ~74.8%. Thus the headline return is not broad cross-sectional evidence.

Regime decomposition also argues against rescue. For the same spec, bear is negative in every inspected year (-11.10% in 2023, -38.29% in 2024, -38.25% in 2025). Bull/sideways strength in earlier years does not persist sufficiently to offset the later degradation, and no regime filter was preregistered.

## Cost / tails audit
Costs behave adversely as required. For `idio_mom_lb168_k1_h4`, 2025 moves from -33.33% base / PF 0.963 / DD -41.63%, to -57.36% severe / PF 0.919 / DD -61.77%, to -82.56% supersevere / PF 0.837 / DD -83.61%. There is no cost-robust edge.

Trade tails are materially wider than the tiny median edge: in the same 2025 base fold p01 is about -2.43%, p50 only +0.005%, p99 +2.30%, with worst trade about -7.71%. Because overlapping sleeves make trade-level diagnostics approximate, portfolio accounting remains authoritative; neither view supports promotion.

## Decision
Reject the entire Phase230 cross-sectional idiosyncratic-momentum family with no rescue, no asset exclusion, no regime cherry-pick, and no grid mutation. Champion remains unchanged. Phase231 was frozen before observing Phase230 and is therefore eligible as the next scientifically distinct test.
