# V98 Independent — Phase136 rejection audit

Decision: **REJECT_NO_RESCUE**.

Phase136 was a frozen, preregistered post-downside-jump next-day rebound hypothesis evaluated only on the 2023-2025 training window. Validation and final holdout remained unopened; V16, V99, and Phase083 were not used for selection.

## Evidence

- Aggregate training return: +110.02%; CAGR 28.06%; PF 1.233; max drawdown -23.72%.
- Fold 2023: +55.73%, PF 1.450.
- Fold 2024: +42.38%, PF 1.305.
- Fold 2025: **-5.99%, PF 0.970**. This independently violates the frozen positive-fold and PF>=1.02 requirements.
- Severe costs: +83.79%, PF 1.191. Supersevere: +47.92%, PF 1.126. Cost stress therefore does not explain the rejection.
- Regime return-sum approximation is positive in bear (+0.2735) and bull (+0.5379), but nearly flat in sideways (+0.0178), consistent with weak robustness outside directional regimes.
- Concentration is not the primary failure: mean top-1 weight share 20.91%; p95 23.29%; mean active assets 3.17. Positive contribution shares are distributed across all five assets, largest SOL at 33.73%.
- Tail dependence is material but not dominant enough to rescue the fold failure: top-10 positive days contribute 11.40% of positive-day gains; worst day -6.07%, best day +10.46%.
- Execution guard recorded max open gross 0.5000132 versus frozen 0.50 cap. This is a separate implementation/gross invariant failure and is not waived.

## Failure mechanism

The hypothesis has genuine-looking aggregate expectancy and survives punitive costs, but that expectancy is not chronologically stable. The 2025 fold reverses sign and falls below PF 1.0, while sideways contribution is nearly absent. Because the parameters and event definition were frozen before PnL, changing thresholds, holding period, gross, event breadth, or adding a 2025-specific regime filter would be post-hoc rescue and is prohibited.

## Scientific consequence

Phase136 is closed permanently as tested. No validation or holdout access is authorized. The next experiment must be a scientifically distinct family rather than a refinement of the jump-rebound threshold/holding-period/gross parameters.
