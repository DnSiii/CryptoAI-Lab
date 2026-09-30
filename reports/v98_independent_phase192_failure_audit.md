# V98 Independent — Phase192 failure audit

Decision: **REJECT_FAMILY_NO_RESCUE**.

Scope is training-only 2023-01-01 through 2025-12-31. Validation and final holdout remain closed. V16/V99 are not used.

## Evidence

The family shows a recurring chronological pathology: 2024 is strong while 2023/2025 are weak or negative. Examples from the deterministic harvest:

- `b336_m72_h24`: aggregate base +27.72%, PF 1.067, MDD -34.70%; folds 2023 -2.70% / PF 1.018, 2024 +55.62% / PF 1.220, 2025 -15.71% / PF 0.949. Severe -31.05% / PF 0.971 / MDD -45.33%; supersevere -73.93% / PF 0.839 / MDD -78.00%.
- `b168_m72_h24`: aggregate base +21.75%, PF 1.059, MDD -39.08%; folds 2023 -6.87%, 2024 +74.70%, 2025 -25.22%. Severe -34.29% / PF 0.966; supersevere -75.17% / PF 0.837.
- `b336_m24_h12`: aggregate base +54.47%, PF 1.095, but 2025 -20.29% / PF 0.890 and MDD -43.49%; severe -58.80% / PF 0.904 and supersevere -94.99% / PF 0.677.

The apparent aggregate edge is therefore not chronologically stable and is not cost robust. All eight preregistered specifications fail. No rescue/tuning is scientifically justified.

## Independent pathology audit

- **Regimes:** residual momentum is repeatedly positive in bull but weak/negative in sideways; some variants also lose in bear. Regime breadth is not dependable.
- **Costs/turnover:** severe and supersevere economics collapse across the grid, demonstrating that the weak gross edge is insufficient relative to turnover.
- **Tails:** top/bottom-10 shares are roughly 8–12%, so rejection is not explained by a tiny number of extreme days.
- **Concentration:** instantaneous top-1 share is structurally 50% because the design holds one long and one short; asset contribution is often dominated by SOL (~38–53% in representative variants). This is not the primary failure, but reinforces fragility.
- **Drawdown:** base MDD is generally ~35–49%, becoming ~45–75% severe and ~78–97% supersevere in representative variants.
- **Reproducibility:** workflow executed twice with byte-identical report SHA256 `8d8413afaf189b45455a69b473c92cb1c055b2332cad7fccf07e23d8f3caa5c9`.
- **Data boundary:** canonical rebuild ended 2025-12-31 23:00 UTC; explicit workflow assertion verified no 2026 observations.

## Research implication

Do not tune beta/momentum/rebalance parameters further. The evidence rejects this residual-momentum family under the preregistered gates. The next hypothesis must be scientifically distinct and should address the repeated observation that cross-sectional trend families are unstable across 2023/2024/2025 and highly cost-sensitive.
