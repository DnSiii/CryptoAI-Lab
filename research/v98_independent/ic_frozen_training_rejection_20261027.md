# IC immutable historical training rejection — 2026-10-27

**Decision: REJECT_IC_HISTORICAL_GROWTH_OR_MARGINAL.** This is a frozen 2023–2024 historical result, not a validated, benchmarked or tradable V98. No 2025 holdout, 2026+, XRP, V14/V15/V99, Frozen or paper accessed.

## Reproducible source and settlement evidence

- Preregistration: `ic_oi_crowding_prereg_20261027.md` (before signal implementation).
- [Independent native OI source audit](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40477926560): 3,011/3,048 verified Clean-4 asset-days, 37 quarantined asset-days, 72,264 authenticated OI hours; missing hours are never filled.
- [Official IC seven-slot 30-cell workflow](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40478203424): source-only viability PASS; financed epochs in 2023/2024: Core 27/26, Opportunity 13/19, Relative Value 25/24, Stress/Recovery 18/22. Thirty of thirty independently funded USD10k physical books passed; cross-Ubuntu numerical reproducibility true, zero reconciliation errors; independent settlement replay passed five paths, each 105,258 hours and 13,152 funding-event-hours.
- [Immutable artifact-only economic first-fault readout](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40478499771): original economic summary only, no strategy rerun or holdout.

## Frozen IC full historical economics (USD10k, carried-before-fill)

| Measure | Base | Severe |
|---|---:|---:|
| Two-year CAGR | +61.8418% | +55.9075% |
| 2023 return | +80.9539% | +74.3160% |
| 2024 return | +44.8438% | +39.5279% |
| Max drawdown | 23.9245% | 25.2375% |
| Turnover (USD) | 351,195.61 | 336,921.90 |
| Native signed funding (USD) | -1,499.14 | -1,424.53 |
| Fees (USD) | 175.60 | 673.84 |
| Slippage (USD) | 175.60 | 1,010.77 |
| Hourly net PF | 1.04326 | 1.03984 |
| Hourly win rate | 51.8926% | 51.8242% |
| Positive UTC days | 374/731 | 372/731 |
| Worst 1% hourly CVaR | -1.4894% | -1.4912% |

## Frozen full-minus-ablation marginal log growth (combined 2023+2024)

| Sleeve | Base | Severe | Precommitted gate |
|---|---:|---:|---|
| Opportunity | +0.018142 | -0.004439 | FAIL; below +0.02 base and negative severe |
| Relative Value | -0.097163 | -0.099065 | FAIL |
| Stress/Recovery | +0.024856 | -0.000799 | FAIL; 2024 marginal below -0.03 |

Full-system positive-year, CAGR, severe drawdown and turnover gates passed; **all three optional marginal gates failed**. Do not reselect a post-hoc ablation, change IC thresholds/signs/windows/gross, or claim a system champion. IC remains rejected. The source and independent physical-accounting infrastructure may be reused by a genuinely distinct, separately preregistered hypothesis, not its rejected trading decisions.

**Critical path:** new complete seven-slot candidate -> training source/causality -> physical and economic gates -> immutable freeze -> independent chronological validation -> only then external benchmark and delivery. No trading authorization.
