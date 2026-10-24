# V98 Independent BO — irrevocable frozen training rejection (2026-10-24)

**Decision: REJECT_BO_HISTORICAL_GROWTH_OR_MARGINAL.** BO is **not** a valid complete V98 engine, is not a champion, and must not be tuned/rescued after these results. Pre-result architecture lock: [BO preregistration](bo_preregistered_architecture_20261024.md). No live/paper trading, no V14/V15/V99 benchmark or signal, no 2025 holdout access.

## Original verified execution
- Initial run 40079787108 failed before economics due to an erroneous workflow CSV asset name `BOBUSDT_1h.csv` introduced by mechanical renaming. Corrected to **BNBUSDT** without changing any source, signals, weights, thresholds or risk logic; original failed run is not economic evidence.
- Original completed economic training: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40079824333, commit `a12594cce23ad160e94da8be617d8e354691278d`.
- **90/90** original physical cells survived; Ubuntu 22.04 and 24.04 agree within the predeclared numeric tolerance. **180/180** cross-OS original receipts passed independent arithmetic checks with zero errors. The successful GitHub workflow exit is *not* a pass of the economic gates.
- Independent raw native signed funding / intrabar replay: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40079897474, commit `a1676269d2b9efe5a7f100a5979f963e5ba72706`. Four original full-path fee/order combinations x 16,272 settlement hours = **65,088** independently checked hourly settlements; all 81 OHLC corner combinations tested per hour. Original 9,144 funding events authenticated; 8,136 training settlement-time native events per path. Replay verified per-event signed cashflow, fees, slippage, margin headroom and units. This is accounting verification, **not** economic or predictive validation.

## Original full portfolio, USD 10,000, carried-before-fill
| Execution | CAGR 2023 | CAGR 2024 | Two-year CAGR | Max drawdown | Fees | Slippage | Native funding |
|---|---:|---:|---:|---:|---:|---:|---:|
| Base | +5.017% | +1.843% | **+3.416%** | 31.51% | $241.19 | $241.19 | -$24.34 |
| Severe | -1.348% | -4.911% | **-3.148%** | 35.19% | $927.39 | $1,391.09 | -$50.03 |
| Supersevere | -16.342% | -21.356% | **-18.891%** | 49.08% | $2,021.07 | $4,042.14 | +$21.74 |

Base notional turnover: **$482,384.06**, 59 hourly fill events. Severe turnover: **$463,695.52**, 60 hourly fill events. Costs are not negligible even with frozen units.

## Mandatory marginal net log-growth, original full minus original sleeve ablation, USD 10,000
| Sleeve | 2023 base | 2024 base | 2023 severe | 2024 severe |
|---|---:|---:|---:|---:|
| Opportunity | **-0.532180** | +0.318834 | **-0.578616** | +0.314311 |
| Relative Value | **-0.015872** | +0.011807 | **-0.024024** | +0.010946 |
| Stress/Recovery | **-0.000789** | **-0.103903** | **-0.004798** | **-0.076725** |

Each sleeve fails the immutable both-years positive marginal criterion. The original native carry gate and 1% ex-ante severe roundtrip budget did **not** ensure predictive positive contribution. Opportunity was especially destructive in 2023; stress in 2024; RV modest and sign-inconsistent. Severe annual full returns are negative. These are observed **training-only** effects, not independent future performance. No post-result sign, lookback, threshold, asset, cost or gross-exposure changes are allowed to rehabilitate BO.

## Scope, integrity, next critical path
Pinned Clean-4 BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT 1h Dec2022–Dec2024 only; native V98 funding and conservative marks, two funding orders, 3 fee tiers, 3 capital scales. **2025 future holdout sealed**, 2026+ excluded, XRP quarantined, contaminated Phase083 excluded. V16/V99 Frozen and V99 paper untouched; all commits only on `research/v98-independent-zero` in V98 namespaced files.

Next candidate, if researched, must be a **genuinely distinct full seven-slot economic architecture** with causal *marginal contribution* and low-turnover economics engineered into the complete portfolio, not a refit of BO. A sensible research direction is an online cost-aware allocation to uncorrelated exposures, but it must be preregistered as a new independent hypothesis, not calibrated to the rejected BO output. No V98 promotion until chronological training, separate untouched validation, native event audit, all gates and only then external benchmark.
