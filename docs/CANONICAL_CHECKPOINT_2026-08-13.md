# CryptoAI V13 PIT Carry-Core — canonical checkpoint

## Status

This directory is the source-backed continuation of the ChatGPT Work research run.
It is separate from the independently reconstructed candidate in PR #1, which was
correctly rejected and must not be represented as a reproduction of this model.

- Mode: `RESEARCH_ONLY` / `PAPER_ONLY`
- Real-order execution: absent
- Real-money approval: no
- Forward paper trading: not started

## Objective

Maximize net compound portfolio growth: lose relatively little when wrong, exploit
winners when right, and reinvest gains, while keeping the probability of catastrophic
loss at a responsible level. The final system is not restricted to spot and may use
long/short futures and controlled leverage. Low activity or a 1%–3% monthly target is
not accepted as the final objective.

## Exact candidate

Configuration: `config/candidate_v13_pit_carry_core.json`

- BTC/ETH regime core: component IDs 1428, 1434, 1745; weight 70%
- Point-in-time funding carry: component ID 356; weight 30%
- Hourly Binance USD-M prices and archived funding
- Signal at close; execution at next open
- Base one-way cost: 0.07%
- Severe one-way cost: 0.12%
- Risk target: 45% annualized volatility
- Target gross leverage cap: 1.5x

Canonical report: `reports/candidate_v13_pit_carry_core_exact.json`

| Replay | CAGR | Max drawdown | Ruin |
|---|---:|---:|---:|
| Exact base | 68.18% | -31.52% | No |
| Severe cost | 53.01% | -37.10% | No |
| Additional 3h delay | 64.56% | -30.48% | No |

All calendar years from 2021 through the available 2026 interval were positive in the
base replay. The 24 rebalance phases produced 67.99%–71.73% CAGR in the phase screen,
with no simulated ruin. The current engine tests pass.

## Honest disclosure

The full historical interval participated in iterative post-holdout research. These
results are robustness evidence, not a pristine untouched holdout. A genuinely new
forward paper interval remains mandatory before real capital.

## Unresolved gates

The candidate is not final. The next work must:

1. explain and correct gross exposure reaching 1.672x despite a 1.5x target cap;
2. run a documented bootstrap/ruin analysis on the exact candidate;
3. run extreme transaction-cost and adversarial-funding scenarios;
4. remove assets and components individually, including delisted-contract stresses;
5. investigate severe-cost drawdown of -37.10%;
6. repeat all critical tests after any correction or improvement;
7. preserve every rejection instead of selecting only favorable variants.

Promotion requires more than crossing headline CAGR. The model must survive the full
adversarial suite and then complete forward paper trading before any real-money path is
considered.
