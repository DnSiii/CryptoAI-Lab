# V98 Independent IY — permanently frozen historical training rejection (2026-10-27)

**Decision: REJECT_IY_HISTORICAL_ALL_THREE_SLEEVES_NEGATIVE_MARGINAL.** The preregistered inverse-vol growth core + 48h acceleration opportunity + signed native funding spread long/short relative-value + convex stress/recovery seven-slot engine is **rejected** as a complete V98 candidate. Do not repair or tune IY's sign, funding pair, thresholds, window, weights, gross, universe, source, execution or cost after the result. Do not promote any physical minus-sleeve book or the Core-only ablation. No 2025 validation, future holdout, external V14/V15/V99 benchmark, paper or live authorization.

## Locked provenance and scope
- [Immutable IY preregistration before code/PnL](https://github.com/DnSiii/CryptoAI-Lab/blob/research/v98-independent-zero/research/v98_independent/iy_funding_spread_convexity_prereg_20261027.md), prereg commit `f2f99efbc06af87ace575733d202763d8916fa27`. Implementation commit `362f503a11347ad4f7bbf3f8e1467049c67d61af`; workflow matrix typo fix `a74e530eece748db7643f21aa29e425a62eaccc5` **before economic PnL**, no changes to economic formulas.
- [Canonical 2023–2024 training run 40589345127](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40589345127): GitHub Actions **success** indicates mechanical execution, **not** economic acceptance. Pinned native Clean-4 source run `40064588623`, manifest SHA256 `833013a2e18836a203afd267ca698175907cff8f4c153c919a7811f14cb80752`. Dec-2022 warmup, BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT, Binance USD-M 1h OHLC/quote, native signed funding/mark, exact timestamp/hash checks. XRP quarantined; 2025/2026+, Phase083, external engines and paper unopened.
- Source-only causal future mutation, zero quote quarantine and budget conservation **PASS**; 2023 financed epochs Core/Opp/RV/Stress 27/27/27/27; 2024 26/24/24/24.
- Five independent USD10k physical books x three cost modes x two funding orders = **30/30 solvent configurations**, 15 economically distinct cases because funding orders coincide; Ubuntu 22.04/24.04 numerical reproducibility PASS; original-artifact-only audit **errors []**.
- Five separate all-settled-hour signed native funding/mark oracle replays **PASS**, respectively Full 104406, Core 105258, minus-Opp 105156, minus-RV 105126, minus-Stress 104402 settled-hour operations (524348 audit operations total, **not trades**); 65510 funding-event-hour verification operations (**not independent market samples**).
- Independently downloaded the original five Ubuntu 24.04 physical book ZIPs and recalculated annual log growth, full-minus-ablation margins, 2023/2024 NAV continuity, native costs and final NAV; agreement with official summary.

## Historical training only — full IY USD10k book
| Metric | Base | Severe | Supersevere |
|---|---:|---:|---:|
| Two-year CAGR | **+68.1596%** | **+61.9215%** | +47.805% |
| 2023 net return | +70.3028% | +63.5928% | see raw receipts |
| 2024 net return | +66.1616% | +60.3730% | see raw receipts |
| Final NAV | USD28297.79 | USD26235.86 | USD21857.98 |
| Max drawdown | 26.5360% | 27.4776% | 29.667% |
| Turnover USD | 344889.97 | 325434.62 | 283720.50 |
| Signed native funding USD | -1064.53 | -983.56 | see raw receipts |
| Hourly net Profit Factor | 1.04895 | 1.04568 | see raw receipts |
| Hourly net payoff | 0.96737 | 0.96814 | see raw receipts |
| Hourly win rate | 52.0230% | 51.9253% | see raw receipts |
| Positive UTC days | 387/731 | 382/731 | see raw receipts |
| Worst 1% hourly CVaR | -1.6183% | -1.6064% | see raw receipts |
| Peak single-asset gross concentration | 66.5845% | 66.5845% | see raw receipts |

## Independently reproduced marginal net log growth, Full minus its own independently funded ablation
| Sleeve | Base 2023 | Base 2024 | Base combined | Severe 2023 | Severe 2024 | Severe combined | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| Opportunity | -.165569 | +.079019 | **-.086550** | -.169255 | +.074002 | **-.095254** | FAIL |
| Relative Value | -.138489 | +.007106 | **-.131383** | -.145636 | -.002275 | **-.147910** | FAIL |
| Stress/Recovery | -.084729 | -.019561 | **-.104290** | -.095504 | -.033005 | **-.128509** | FAIL |

All three optional sleeves fail the **precommitted combined >+.02 and each-year >=-.03** criteria under both base and severe costs. Base/severe full annual positivity, CAGR, drawdown, turnover, physical solvency, source and reproducibility gates pass, but cannot compensate failed economic contribution. Under supersevere costs, all three combined marginals are also negative: Opportunity -.124741, Relative Value -.187678, Stress/Recovery -.188784.

## Physical first-fault attribution — no post-result rescue
- Core-only independently funded base CAGR **+78.7258%**, terminal USD31968.30, turnover USD55367.17; Full base CAGR **+68.1596%**, terminal USD28297.79, turnover USD344889.97. Full finishes **USD3670.51 below Core-only**, while its drawdown improves from 28.3222% to 26.5360%. This is a **growth failure**, not a risk-gate victory.
- Full base versus Core-only native funding improved **USD1074.27** (less negative), but combined fees/slippage increased **USD289.52** and price/exposure opportunity cost outweighed the carry benefit. The funding spread did **not** deliver a positive physical portfolio marginal contribution.
- Full minus-Opp/ minus-RV/ minus-Stress independently funded ablations finish respectively USD2558.29 / USD3973.15 / USD3110.55 **above Full** in base costs. These are diagnostic books of a rejected architecture, **not new candidates**.

## Decision and critical path
**IY permanently rejected and frozen.** No V98 complete engine internally approved; 2025 chronological validation, untouched future holdout and external benchmark remain unopened. Further research must be a **genuinely distinct portfolio-level growth allocation mechanism** that pays for optional sleeves' opportunity cost against Core under native costs, rather than another cosmetic sign/window change to rejected IY or prior books. Repeated 2023–2024 hypothesis attempts materially increase multiple-testing/selection risk. Do not claim historical training CAGR as future expected return or authorize real orders.
