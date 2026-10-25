# V98 Independent DO — frozen capital-efficiency diagnosis (2026-10-25)
Artifact-only audit from run **40182782378**, independent forensics run **40182935999**. DO remains **REJECTED**; this file does not revise its source, preregistration, gates or historical decision. No PnL rerun, 2025 read or external benchmark.

## Native economic decomposition, USD 10k, carried-before-fill
| Metric | Core-only base | Full base | Core-only severe | Full severe |
|---|---:|---:|---:|---:|
| Two-year CAGR | 11.55% | 16.47% | 3.70% | 9.10% |
| 2023 net return | 8.03% | 24.57% | 0.74% | 17.01% |
| 2024 net return | 15.21% | 8.91% | 6.75% | 1.73% |
| Fees + slippage (USD) | 388.31 | 410.00 | 1765.58 | 1875.00 |
| Funding (USD) | -592.60 | -491.82 | -538.04 | -443.38 |
| Turnover (USD) | 388308 | 409995 | 353115 | 375000 |

Full base: max gross/NAV **0.7433**, max single-asset concentration **0.9153**, hourly PF **1.0184**, payoff **0.9975**, win rate **50.52%**, positive UTC days **342**, 1% hourly CVaR **-1.371%**. Full severe: max gross/NAV **0.7381**, concentration **0.9191**, hourly PF **1.0107**, payoff **0.9918**, win rate **50.47%**, positive UTC days **341**. These are historical training receipts, not live forecasts.

## Strict leave-one-out marginal log growth (full minus removed)
| Sleeve | 2023 base | 2024 base | 2023 severe | 2024 severe |
|---|---:|---:|---:|---:|
| Opportunity | -0.073974 | -0.006386 | -0.074313 | -0.006400 |
| Relative Value | +0.000356 | -0.040956 | +0.006479 | -0.034222 |
| Stress/Recovery | +0.096822 | -0.041396 | +0.103021 | -0.040095 |

**Decision-critical observation:** Full system improves on core-only over both years but every satellite fails strict annual marginal gates; Stress improves 2023 and damages 2024, while Opportunity is negative in both. At the same time peak authorized gross is <0.75 NAV despite much larger requested budgets, so adding nominal leverage or more signals is not a justified route to CAGR; authorized physical capacity and net edge per unit are the binding economics. Native friction is material (severe fees/slippage USD1875 vs initial USD10000).

Next **genuinely distinct** architecture should preregister a system-level causal hypothesis addressing the poor per-unit growth, turnover and concentration under unchanged physical survival constraints, rather than relaxing gates or cosmetically changing DO. Preserve 2025 holdout, Frozen and paper.
