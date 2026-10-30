# CryptoAI V13 — paper-gate checkpoint

## Decision

The historical finalist is approved to **start forward paper trading only**.
Real-money execution remains absent and unauthorized.

## Finalist

- Core: BTC/ETH regime ensemble plus point-in-time funding carry.
- Target cap: 1.35x; close gross guard: 1.5x.
- Circuit breaker: after a 15% portfolio drawdown, exposure is halved for 14
  days; the decision uses only the previous close and executes no earlier than
  the next open.

## Exact historical evidence

| Scenario | CAGR | Max drawdown |
|---|---:|---:|
| Base | 60.14% | -28.82% |
| Severe costs | 48.82% | -30.54% |
| 3-hour delay | 56.15% | -28.54% |
| Adverse funding | 46.81% | -28.87% |
| Severe costs + adverse funding | 34.81% | -33.96% |

All base calendar intervals from 2021 through July 2026 were positive. The
engine passed 18 automated tests, including reference/fast equivalence,
causality, intrabar liquidation, gross guarding, funding stress and forced exit
from an untradable contract.

## Synthetic risk

The dynamic circuit breaker was reapplied inside every synthetic path. Across
30,000 paths for each combination of 7/14/30-day blocks and 3/5-year horizons
(180,000 paths total), no simulated ruin was observed. This is `0 observed`,
not a guarantee of zero true probability.

## Concentration disclosure

The model is meaningfully dependent on BTC, ETH and the combination of the core
with carry. Removing BTC reduced historical CAGR to 35.70%; removing ETH to
33.78%; core-only produced 43.16%; carry-only produced 30.12% with substantially
worse drawdown. This concentration is accepted for paper evaluation because
BTC and ETH are the deepest markets, but it is not described as broad
diversification.

## Research limitation

All available history participated in iterative research. No historical result
is a pristine holdout. The next valid evidence must come from timestamps newer
than the model-freeze boundary set on 13 August 2026 by
`scripts/paper_once_v13.py`; later backfills of earlier dates are excluded.
