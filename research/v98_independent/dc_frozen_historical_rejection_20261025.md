# V98 Independent DC — frozen complete historical rejection (2026-10-25)

**Decision: REJECT_DC_HISTORICAL_GROWTH_OR_MARGINAL.** DC is permanently rejected as a seven-slot trading engine. Do not retune its source, signs, carry pair, windows, budgets, regime logic, core/secondary partition, governor or gates. No holdout or real trading.

## Ex-ante chronology and independent execution evidence
- Pre-result architectural preregistration: commit `423dc8b646d1cdf1df6f2952766da2aea074cb06`.
- Authenticated Clean-4 2022-12 warmup / 2023-2024 training source + 20-cell native physical execution: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40159679454 .
- Independent artifact-only marginal, PF, cost and tail diagnosis: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40159808406 .
- Independent artifact-only core capital opportunity-cost audit: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40159855542 .
- Causal future-perturbation PASS; source gate PASS. 2023/2024 effective epochs: Core 26/29, Opportunity 20/17, Relative Value 51/52, Stress/Recovery 21/20.
- Five paths x USD10k x base/severe x both funding orderings = **20/20 native physical cells survived**, Ubuntu 22.04/24.04 reproduced, independent artifact-only audit errors=[]; independent event-level ledger replay NOT performed.

## Full historical training, carried-before-fill
| Metric | Base | Severe |
| --- | ---: | ---: |
| Two-year CAGR | +52.3750% | +40.2702% |
| 2023 net return | +89.1656% | +71.9927% |
| 2024 net return | +22.8106% | +14.4517% |
| Max drawdown | 21.7709% | 21.4000% |
| Hourly PF | 1.05090 | 1.04158 |
| Hourly payoff | 1.00567 | 0.99929 |
| Hourly win rate | 51.100% | 51.036% |
| Positive UTC days | 52.257% | 50.889% |
| Peak gross/NAV | 0.77041 | 0.76473 |
| Peak single-asset concentration | 83.20% | 83.13% |
| Signed native funding, USD10k start | −$522.57 | −$440.86 |
| Fees | $344.12 | $1,217.43 |
| Slippage | $344.12 | $1,826.15 |
| Turnover | $688,232 | $608,715 |
| Physical fill hours | 103 | 103 |

## Annual full-minus-ablation marginal net log growth (carried-before-fill)
| Sleeve | 2023 base | 2024 base | 2023 severe | 2024 severe | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Opportunity | +0.02673998 | +0.00836208 | +0.02895553 | +0.02787904 | FAIL: 2024 under new-after-fill |
| Relative Value | −0.04092746 | −0.20848812 | −0.12208134 | −0.16509162 | FAIL: both years, both orders |
| Stress/Recovery | +0.00027644 | −0.13745562 | −0.00942944 | −0.13471557 | FAIL |

The second native funding order also failed all three marginal gates. Growth, severe drawdown, survival, and cross-OS reproducibility gates passed, but that **does not** approve the composed engine.

## Independent physical capital opportunity-cost audit
- Core-only CAGR base **+62.6429%**, complete **+52.3750%** (−10.2679 percentage points). Severe core-only **+47.4654%**, complete **+40.2702%** (−7.1952 points).
- Full-minus-core net log growth **2023 / 2024**: base **−0.194873 / +0.064359**; severe **−0.201799 / +0.101685**. The satellites helped the complete portfolio in 2024 but reduced net compounding in 2023; no across-year robustness.
- Core-only versus full peak gross/NAV base **0.78688 vs 0.77041**, turnover **$849,890 vs $688,232**; full funding cost less negative (**−$522.57 vs −$1,101.85**), yet two-year compounded growth declined. Neither lower turnover nor lower funding by itself proves positive marginal value.
- RV unconditional native funding spread carry did not overcome price/interaction/collateral opportunity costs; avoid treating source activity as economic alpha.

**Critical path:** the next genuinely distinct V98 candidate should measure *native funding vs price vs physical displacement at event level*, and require independently positive economic contribution of its Relative Value mechanism in chronological training before any holdout. No new candidate may borrow DC rejected signals/parameters. 2025 holdout sealed; XRP quarantined; 2026+ untouched; V14/V15/V99 external benchmarks unopened; Frozen/paper unchanged.
