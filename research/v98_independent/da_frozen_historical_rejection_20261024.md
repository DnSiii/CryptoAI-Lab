# V98 Independent DA — frozen historical rejection (2026-10-24)

**Decision: REJECT_DA_HISTORICAL_GROWTH_OR_MARGINAL.** DA is permanently rejected as a complete seven-slot engine. Do not retune signs, windows, source conditions, budgets, core-idle scales, gross or gates after seeing results. No holdout, external benchmark, scale-up, paper or live.

## Ex-ante and verified chronology
- Preregistered commit `1475e3044ab15072c454c227f5cda4de8bb399cc` before all DA source/physical PnL code.
- Official source + 20-cell historical native run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40156312719
- Independent artifact-only economic diagnosis: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40156420958
- Clean-4 authenticated BTC/ETH/BNB/SOL Binance USD-M 1h 2022-12 warmup through 2024-12, signed native funding/mark. 2025 holdout unopened, 2026+ excluded, XRP quarantined, Phase083 invalid, external V14/V15/V99 unopened.
- Future perturbation static PASS. Effective source epochs 2023/2024: Growth 12/15; Opportunity 17/25; RV 23/31; Stress 35/33. All source gates PASS.
- Five paths x USD10k x base/severe x two funding orders = **20/20 physical cells survived**, Ubuntu 22.04/24.04 reproducibility true, artifact-only audit errors=[]; no independent event-level replay.

## Full historical training (carried-before-fill)
| Metric | Base | Severe |
| --- | ---: | ---: |
| Two-year CAGR | +21.4054% | +14.3713% |
| 2023 net return | +4.7025% | **−0.9183%** |
| 2024 net return | +40.8103% | +32.0445% |
| Maximum drawdown | 34.0941% | 36.1330% |
| Hourly net PF | 1.02442 | 1.01655 |
| Hourly net payoff | 1.00749 | 0.99836 |
| Hourly win rate | 50.417% | 50.451% |
| Positive UTC days | 48.153% | 46.922% |
| Peak gross/NAV | 0.77686 | 0.77172 |
| Peak single-asset concentration | 100% | 100% |
| Signed native funding (USD10k start) | -$676.38 | -$626.83 |
| Fees | $192.33 | $722.86 |
| Slippage | $192.33 | $1,084.30 |
| Turnover | $384,659.84 | $361,432.43 |

## Annual full-minus-ablation marginal log growth, carried-before-fill
| Sleeve | 2023 base | 2024 base | 2023 severe | 2024 severe | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Opportunity | -0.02819810 | -0.00821985 | -0.01044760 | -0.00656395 | FAIL |
| Relative Value | -0.11642253 | -0.03023613 | -0.10315226 | -0.03872746 | FAIL |
| Stress/Recovery | -0.28974629 | -0.01578714 | -0.27108933 | -0.01017523 | FAIL |

Second funding ordering also fails all three. Full growth and all satellite annual marginal gates fail. **Core-capacity complementarity did not rescue portfolio economics** and is not a promoted architecture. DA is distinct from CZ, which also failed its marginal gates despite +84.01% base training CAGR. Neither is a valid V98.

**Critical path:** stop repeating low-contribution satellites; require genuinely orthogonal positive net economic mechanisms and examine physical opportunity cost, exposure concentration, and native funding before another preregistered complete portfolio. Keep Frozen, V99 paper/workflows/reports and 2025 holdout untouched. No trading authorization.
