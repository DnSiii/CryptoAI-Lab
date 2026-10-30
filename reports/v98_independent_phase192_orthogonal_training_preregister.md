# V98 Independent — Phase192 preregistration

## Status

**PREREGISTERED / TRAINING ONLY / DO NOT TUNE AFTER RESULTS**

Final holdout remains closed. Validation remains closed. V16 and V99 are prohibited from selection, tuning, rescue, interpretation, or comparison-driven parameter choice.

## Scientifically distinct hypothesis

**Cross-sectional idiosyncratic momentum after market-beta removal.**

Phase191 asked whether raw cross-sectional trend persists specifically under low realized volatility. Phase192 instead removes the common crypto-market component first and tests whether *residual* relative momentum persists. The economic hypothesis is that asset-specific information diffuses more slowly than market-wide moves; ranking residual momentum may therefore avoid the unstable market/regime exposure observed in prior raw-trend families.

This is not a rescue/inversion of Phase191. No low-volatility gate is used.

## Frozen construction

Universe: the existing V98 Independent canonical five-asset universe only.

Training window: 2023-01-01 through 2025-12-31 only.

At each hourly timestamp, using only information available through that timestamp:

1. Compute hourly log returns for each asset.
2. Define the contemporaneous equal-weight market return across available assets.
3. For each asset estimate rolling beta to the equal-weight market using only trailing observations.
4. Residual return = asset return - rolling beta * market return.
5. Sum residual returns over the frozen residual-momentum lookback.
6. At each rebalance, long the asset with the highest residual momentum and short the asset with the lowest residual momentum, equal gross legs (dollar-neutral target). Hold until next rebalance.
7. Positions must be shifted so no return used to construct/rank the signal is earned by the position at that same timestamp.

## Frozen grid — exactly 8 specifications

- beta lookback hours: `{168, 336}`
- residual momentum lookback hours: `{24, 72}`
- rebalance hours: `{12, 24}`

Cartesian product = 8 specs. No additional thresholds, regime filters, direction flips, rescue grids, or post-result variants are allowed.

## Required evaluation

For every spec report:

- aggregate total return, CAGR, max drawdown, Profit Factor, payoff, win rate, positive/negative days, best/worst day, p01/p05/CVaR05;
- turnover, average/max gross and max absolute net exposure;
- chronological folds 2023, 2024, 2025 separately;
- realistic funding and transaction costs under base, severe, and supersevere assumptions inherited unchanged from V98 Independent evaluation infrastructure;
- bull/bear/sideways regime decomposition;
- asset contribution shares;
- top-1 concentration and positive/negative tail concentration;
- reproducibility by two byte-identical executions;
- data-boundary invariant proving no observation >= 2026-01-01 is available to this training experiment.

## Frozen promotion discipline

A candidate can be promoted from training only if it satisfies the existing V98 Independent economic/risk gates simultaneously, including positive robust edge under cost stresses, acceptable drawdown/risk invariants, chronological fold consistency, regime breadth, concentration/tail limits, and deterministic reproducibility.

If no specification passes all frozen gates: `REJECT_FAMILY_NO_RESCUE` and do not open validation.

If exactly/multiple specs pass, select only by the already-frozen V98 gate/ranking discipline; freeze the selected specification before any validation data are built or inspected.

## Anti-overfit / isolation

- No V99 files, results, workflows, paper state, or frozen engines may influence Phase192.
- No V16 Frozen files/results may influence Phase192.
- No 2026 validation or final-holdout observations may be built or inspected during training selection.
- No parameter changes after Phase192 economic results are observed.
- Any future hypothesis after rejection must be scientifically distinct and separately preregistered.
