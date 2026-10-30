# V98 Independent CY — frozen historical economic rejection (2026-10-24)

**Decision: REJECT_CY_HISTORICAL_MARGINAL.** CY is permanently rejected as a complete composed engine. No post-result retuning of source signs, windows, thresholds, online marginal gates, budgets or gross exposure; do not cosmetically rescue CY.

## Preregistered and verified evidence
- Preregistration commit `4bdc429d1dcff55453839c49ea6c7048bc5f3505` preceded all CY source and PnL code.
- Official native historical run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40152185077 . Source gate PASS: 2023/2024 effective epochs Growth 21/20; Opportunity 51/49; Relative Value 51/52; Stress/Recovery 31/32. Future perturbation causal check PASS.
- Pinned Clean-4 BTC/ETH/BNB/SOL 1h Dec-2022 warmup through 2024-12 only, native signed funding and mark bounds. XRP quarantined, 2025 untouched, 2026+ excluded.
- 5 paths x USD10k x base/severe x two funding orderings, reproduced on Ubuntu 22.04/24.04: **20/20 physical cells survived, cross-OS reproducibility true, artifact-only accounting errors=[]**. No independent event-level replay.
- Full base historical two-year CAGR **+50.6507%**, severe **+41.3260%**; base annual returns 2023 **+83.2757%**, 2024 **+23.9028%**; severe 2023 **+72.6858%**, 2024 **+15.7160%**. Base DD **38.2991%**, severe DD **39.7396%**. Full positive annual log growth, base/severe CAGR and severe DD gates passed.
- USD10k base native funding -$1,969.60, fees $243.92, slippage $243.92, turnover $487,849.34, 103 fill hours; severe funding -$1,807.21, fees $898.03, slippage $1,347.04, turnover $449,013.43, 103 fill hours. Base hourly PF 1.04131, payoff 0.98730, win rate 51.331%, positive UTC days 48.974%. Severe PF 1.03500, payoff 0.98565, win rate 51.221%, positive days 48.564%.

## Preregistered annual full-minus-ablation marginal log growth
`carried_before_fill` funding order, values are log growth differences (not CAGR):
| Sleeve | 2023 base | 2024 base | 2023 severe | 2024 severe | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Opportunity | +0.12090 | -0.03927 | +0.11924 | -0.04999 | FAIL |
| Relative Value | -0.09020 | -0.03823 | -0.10590 | -0.04558 | FAIL |
| Stress/Recovery | +0.09060 | +0.08691 | +0.08681 | +0.08359 | PASS |

The second funding order reproduces the same sign failures. **CY fails Opportunity 2024 and RV both years.** CY must not be scaled, benchmarked or evaluated on the 2025 holdout.

## Critical path
Two genuinely distinct composed architectures CX and CY passed physical/reproducibility/high-growth gates but failed annual marginal contribution, especially RV. Future work must test an independently preregistered economically orthogonal RV mechanism **inside a new complete portfolio** without reusing or altering rejected CX/CY experiments. No paper/live authorization. V16/V99 Frozen, V99 workflows/reports/paper and 2025 holdout preserved.
