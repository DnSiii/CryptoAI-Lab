# IH permanently rejected — original native physical training, 2026-10-27

**Decision: REJECT_IH_HISTORICAL_GROWTH_OR_MARGINAL.** No parameter, sign, threshold, budget, gross, risk, regime or ablation rescue. No promotion of IH or its individual modules. The 2025 holdout, 2026+, V14/V15/V99 internals, Frozen and paper remain untouched.

## Immutable preregistration and source
- IH was preregistered at commit `33324102db9541f4245822d70a1cfce924f00805` **before** signal implementation and PnL.
- [Original 30-cell run](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40498319310), Clean-4 pinned USD-M Dec-2022 warmup / 2023–2024 native OHLC, quote, mark, funding only; no 2025 or later.
- Pre-economic source gate passed, causal future-mutation and zero-quote quarantine passed. Financed epochs 2023 Core/Opp/RV/Stress 27/8/18/27; 2024 26/16/17/25.
- All 30/30 actual-open physical cells survived, Ubuntu 22.04/24.04 reproduced, zero independent artifact reconciliation errors. The independent settlement oracle jobs are additional mechanical checks and do not change the economic rejection.
- [Original artifact-only economic first-fault audit](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40498596146), no recomputation or post-result rescue.

## Frozen historical training USD10k, 2023–2024
| Metric | Base | Severe |
|---|---:|---:|
| Two-year CAGR | +82.0157% | +75.6264% |
| 2023 net return | +144.7934% | +134.3901% |
| 2024 net return | +35.4485% | +31.6968% |
| Maximum drawdown | 30.6298% | 31.0836% |
| Turnover USD | 373,654.82 | 351,812.19 |
| Signed funding USD | -1,735.98 | -1,633.97 |
| Fees USD | 186.83 | 703.62 |
| Slippage USD | 186.83 | 1,055.44 |
| Hourly PF | 1.04506 | 1.04274 |
| Hourly payoff | 0.98358 | 0.98386 |
| Hourly win rate | 51.5153% | 51.4525% |
| Positive UTC days | 380/731 | 377/731 |
| Hourly CVaR 1% | -1.7226% | -1.7125% |
| Peak asset concentration | 75.0499% | 75.0499% |

## Physical full-minus-ablation net log growth
| Sleeve | 2023 base | 2024 base | Combined base | 2023 severe | 2024 severe | Combined severe | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| Opportunity | +0.097369 | -0.007211 | +0.090157 | +0.095225 | -0.008121 | +0.087104 | PASS |
| Relative Value | +0.126933 | -0.007665 | +0.119268 | +0.123965 | -0.009980 | +0.113985 | PASS |
| Stress/Recovery | -0.083323 | -0.055003 | -0.138326 | -0.095612 | -0.060068 | -0.155680 | **FAIL** |

All four base/severe funding-order annual growth gates passed, as did the base/severe full CAGR, severe drawdown and turnover gates. **Stress/Recovery has a negative marginal contribution in both years and both fee modes**, decisively falsifying the complete composed architecture despite strong in-sample CAGR. No external benchmark comparison, validation pass, holdout read, live orders or paper authorization.

Next architecture must be economically distinct and independently preregistered. This document is a frozen rejection, not a development roadmap for IH rescue.
