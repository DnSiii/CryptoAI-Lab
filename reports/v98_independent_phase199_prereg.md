# V98 Independent — Phase199 preregistration

Status: FROZEN BEFORE IMPLEMENTATION/RESULTS.

## Hypothesis
Persistent cross-sectional funding pressure can identify crowded perpetual positioning whose subsequent relative return mean-reverts. At each decision timestamp, rank eligible assets by a lagged funding-pressure score. Short the highest positive-pressure tail and long the lowest/negative-pressure tail, dollar-neutral.

This is scientifically distinct from Phase198: trigger comes from funding pressure, not residual price shocks.

## Causality and universe
- All features at decision t use observations available no later than t-1.
- Training-only boundary: timestamps < 2026-01-01 UTC.
- Validation and final holdout must remain unopened.
- No V16/V99 code, reports, state, parameters, paper results, or selection evidence.
- Universe eligibility must be determined causally from information available at t-1; no future-survival filter.

## Frozen grid
Funding aggregation lookback: {24h, 72h}.
Cross-sectional extreme tail: {20%, 30%} on each side.
Holding/rebalance horizon: {8h, 24h}.
Total grid: 8 specifications. No post-result threshold additions or inversion rescue.

Score: trailing mean funding rate over frozen lookback, shifted one observation before ranking. Long lowest funding-pressure tail; short highest funding-pressure tail. Equal weight within each side; target gross 1.0, net 0.0 when both books are available. If minimum breadth for both books is unavailable, remain flat rather than relaxing selection.

## Evaluation contract
Chronological training folds: calendar 2023, 2024, 2025 plus pooled training evidence. Preserve the repository's established realistic execution costs and realized funding treatment under base, severe and supersevere stress assumptions.

For every spec/stress report: total return/CAGR, max drawdown, Profit Factor, payoff, win rate, positive/negative days, turnover/activity/exposure, yearly folds, bull/bear/sideways regime evidence, tail concentration (including bottom-10 loss share), and position concentration.

## Promotion gates
A candidate can advance only if the pre-existing V98 economic gates pass without reinterpretation: positive robust edge after realistic costs/funding, acceptable MDD, chronological consistency, regime breadth, severe and supersevere survival, sufficient activity, no pathological concentration/tail dependence, and deterministic reproducibility. Zero-activity is failure, never a perfect metric.

Any family-wide failure closes Phase199 as REJECT_FAMILY_NO_RESCUE. Validation/holdout may not be opened to rescue or select a configuration.

## Reproducibility/invariants
Implementation must enforce the <2026 boundary in code, verify causal lagging, produce deterministic sorted output, and be executed twice with byte-identical report hashes before any promotion decision.
