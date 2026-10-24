# V98 Independent BX — frozen historical rejection (2026-10-24)

**Irrevocable decision: REJECT_BX_ECONOMIC_GROWTH_OR_MARGINAL.** BX was preregistered at commit `7394d37a8d094fec3c54db7c739339ec59d03058` **before any BX PnL**. Original 90-cell code/workflow at commit `66f1339e7b35350aa978cd51ade880acc9f837d3`; no post-result retuning or rescue. Official GitHub Actions run **40095800188** (10 matrix jobs plus reconcile), independent native event replay run **40095887569**. All changes confined to V98 Independent namespace and V98-only workflows.

## Official Clean-4 historical training results (NOT forward PnL)

Authenticated Dec2022–Dec2024 BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT Binance USD-M 1h, 9,144 native funding events in original source, 2023 and 2024 chronological evaluation, **2025 future holdout sealed**. Source manifest SHA256 `833013a2e18836a203afd267ca698175907cff8f4c153c919a7811f14cb80752`. All 90/90 original physical scenarios mechanically survived; two independent Linux OS runs agreed; 180/180 original receipts passed independent arithmetic with zero errors; book-to-book isolation/counterfactual invariance passed. Mechanical survival **does not** imply economic success.

| Full BX, carried-before-fill | USD10k CAGR 2023–24 | 2023 net | 2024 net | max DD | |
| --- | ---: | ---: | ---: | ---: | --- |
| Base | **+2.30%** | **−2.53%** | **+7.37%** | 11.66% | Rejected |
| Severe | **−6.08%** | **−6.14%** | **−6.02%** | 18.98% | Rejected |
| Supersevere | **−24.18%** | **−22.98%** | **−25.38%** | 43.56% | Rejected |

Capacity sensitivity, **same original full architecture**: USD1m base CAGR **+10.30%**; USD10m base **+0.68%**. USD10m severe **+0.47%** and supersevere **−0.07%**. Never extrapolate USD10k gains to USD10m or assume liquidity.

USD10k/base original full-book costs: fees **USD242.61**, slippage **USD242.61**, native signed funding **−USD136.86**; severe execution friction **USD2,315.05**, funding **−USD65.46**. Four isolated book final NAVs (base, starting USD6500/1500/1000/1000): Growth **USD6,944.50**, Opportunity **USD1,567.41**, Relative Value **USD974.55**, Stress **USD978.34**. **Core marginal isolation succeeded but growth did not.**

## Original preregistered annual sleeve marginal log growth, USD10k carried-before-fill

| Sleeve | 2023 base | 2024 base | 2023 severe | 2024 severe | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Opportunity | +0.007555 | −0.001093 | +0.003827 | −0.004558 | FAIL |
| Relative Value | −0.003533 | +0.001103 | −0.009581 | −0.004700 | FAIL |
| Stress/Recovery | 0.000000 | −0.002068 | 0.000000 | −0.004275 | FAIL |

No portfolio-level marginal can be rescued by reporting only the profitable year. Unlike BW, BX independently ringfences all four book cash balances and allocates only a quarter of observed physical liquidity to each; the official cross-path audit found **no cross-book NAV or execution contamination**. This demonstrates a real structural accounting fix, not a profitable strategy.

## Independent native-event replay

Original separate run **40095887569** rederived signed funding marks, actual-open gap/close PnL, fees/slippage, and **1,266,030 independent intrabar 81-corner checks** across all six USD10k full-book fee/funding-order combinations. All six passed; maximum settlement difference was at most **4.55e-13 USD**. This validates the recorded cashflow arithmetic conditional on the generated orders, **not** exchange live fills, future PnL, or independent signal profitability. Native replay uses the same causal BX signal/governor for targets; the cashflow/81-corner arithmetic is independently coded.

## Next research decision

Do **not** modify, reclassify or resurrect BX. BX disproves the hypothesis that merely isolating satellites solves growth; it removed BW's core-coupling confound but fixed idle book capital, execution costs and low satellite economic edge prevent strong compounded wealth. Before another expensive full 90-cell architecture, establish a **genuinely distinct, preregistered source-level economic mechanism** with positive net edge after realistic round trips, plus a feasible physical scaling model; avoid arbitrary risk minimization or a new threshold grid. Preserve 2025 holdout, V16/V99 Frozen and V99 paper; no live-trading authorization.

**Status:** no V98 fully validated or approved. Official run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40095800188 ; native audit: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40095887569 .
