# V98 Independent Phase236 — post-mortem

## Mechanical decision
`REJECT_FAMILY_NO_RESCUE` across all eight preregistered residual-kurtosis specs. The decision-grade workflow completed successfully and its independent validator reported zero passing specs.

## Integrity evidence
- Training-only canonical rebuild ended at 2025-12-31 23:00 UTC; workflow firewall asserted no price/funding timestamps >=2026-01-01.
- Causality/grid assertions checked `beta.shift(1)`, `signal.iloc[i-1]`, kurtosis construction, exact 8-spec Cartesian grid and frozen 7/14/28 bp costs.
- Two complete evaluator executions were byte-identical, SHA256 `1b9385130c0546ee6fbea3758ff02a23096c3b59edd8b2f3e7f1757283143f65`.

## Failure mechanism
The family fails economically before any rescue is defensible. Example frozen spec `idkurt_beta168_kurt168_k1_h4`, 2023 base: return -50.32%, max drawdown -65.34%, PF 0.935, payoff 0.919, win rate 50.42%, positive days 47.67%. All three reported regimes were negative: bear -8.79%, bull -31.02%, sideways -21.04%. Severe and supersevere costs worsen the same failure rather than merely turning a marginal edge negative.

Concentration is also material in that example: max absolute asset contribution share ~68.7%, with XRP the dominant loss contributor (-43.53 percentage points of arithmetic PnL contribution) and SOL also strongly negative (-16.09 pp). This supports rejection rather than tuning around a narrow tail/regime pathology.

## Decision discipline
No sign reversal, parameter rescue, extra thresholds, fold averaging, or 2026+ inspection. Phase236 is closed as a rejected family. The next hypothesis must be scientifically distinct and preregistered before any performance observation.