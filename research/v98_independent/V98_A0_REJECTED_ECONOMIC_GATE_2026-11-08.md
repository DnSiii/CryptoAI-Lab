# V98 Independent — A0 economic gate: REJECTED (2026-11-08)

## Immutable evidence
- Branch: research/v98-independent-zero; run 42486732961; head befcd9c394d6dfef921785ebb97381e790c99e48; conclusion SUCCESS (pipeline, not strategy).
- Artifact 13619951753; artifact ZIP SHA256 981b13ca794aef408ac75f8e5aae5004e1870041a6cf6bf04ef36b004323664a.
- Price manifest SHA256 01e7bdeb8bcaf34ee898e322cf20f4479c0e25a9066b40f8cd2446286259f8a8; funding manifest SHA256 f33094dfc065aa862a529d46f36e15f8a418ab085780214a0423488d2ff49622.
- 108192 slot rows / 27048 hourly timestamps, four assets, 2022 warmup through 2025. Prior-hour decisions executed at next open. Holdout not accessed. Three execution-cost scenarios: 1x, 2x, 4x.

## Observed in-sample historical replay (NOT independent validation)
| Cost multiplier | Final equity from $10,000 | CAGR | Max drawdown | Hourly PF | Positive days / 1127 |
|---|---:|---:|---:|---:|---:|
| 1x | $9,967.62 | -0.1051% | -36.27% | 1.0033 | 506 |
| 2x | $5,101.32 | -19.60% | -57.96% | 0.9653 | 473 |
| 4x | $1,335.65 | -47.92% | -88.49% | 0.8945 | 415 |

1x yearly CAGR: 2023 +30.51%, 2024 -5.61%, 2025 -19.54%. Execution costs at 1x: $8,034.68; native funding cashflow -$605.43. 1x hourly win rate 48.89%. Source: successful run job 128750131627, diagnostic output and compound summary.

## Decision and independence
**REJECT A0 in its entirety.** Successful CI/replay does not mean successful strategy. A0 fails growth objective, loses in later chronological calendar slices, and is not robust to severe costs. Do not rescue A0 by tuning signs/windows/thresholds, cost assumptions, gross exposure, or using contaminated holdout. Do not promote as champion, paper, or live engine. No V14/V15/V99 benchmark access authorized yet.

## Next genuine architectural research
Preregister a distinct seven-slot composed hypothesis before examining its returns, emphasizing structural turnover economics and differentiated growth/opportunity/relative-value/stress sleeves; retain causal routing/allocation/governor. Use authenticated Clean-4, native funding, chronological train/validation split and untouched future holdout. Independent reproduction, marginal sleeve contributions, tails/concentration and full cost gates are mandatory before any promotion. Do not reuse rejected A0 parameters as a tuning starting point.
