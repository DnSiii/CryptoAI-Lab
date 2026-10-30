# DK rejected engine — independent frozen-artifact cost and marginal attribution (2026-10-25)

**Artifact-only diagnostic, not DK component promotion.** Official complete 20-cell run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40174485297 . Frozen receipt-only forensic run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40174656075 . No signal change, PnL rerun, 2025, benchmarks, Frozen or paper.

USD10,000 initial NAV, two-year 2023/2024 training, carried-before-fill:

| Full system | Base | Severe |
| --- | ---: | ---: |
| Final NAV | $13,962.49 | $12,100.40 |
| CAGR | +18.1495% | +9.9946% |
| Turnover | $406,962.28 | $372,785.20 |
| Native fees | $203.48 | $745.57 |
| Slippage | $203.48 | $1,118.36 |
| Fees + slippage | $406.96 | $1,863.93 |
| Signed native funding | -$1,279.18 | -$1,167.46 |
| Max drawdown | 29.37% | 32.73% |

Severe-minus-base fees/slippage **+$1,456.96**, with $34,177.07 lower severe turnover. Native funding is a large net expense for both paths; this is not a causal proof that changing funding policy would improve returns.

Marginal annual net log growth (full minus ablation, carried-before-fill):
- Opportunity base: 2023 -0.00191, 2024 +0.00379; severe: 2023 -0.01281, 2024 +0.00732.
- Relative Value base: 2023 +0.01844, 2024 +0.12703; severe: 2023 +0.00077, 2024 +0.13000. **All eight cost/order/year checks passed, but 2023 severe effect is tiny; no selective rescue.**
- Stress base: 2023 +0.06107, 2024 -0.09100; severe: 2023 +0.06419, 2024 -0.09240.

**Decision remains REJECT_DK.** Unlike DJ, DK reduced native turnover and execution friction, but its system-level compounding and severe 2024 growth remain inadequate. The source/ledger is not independently event-replayed, and 2025 holdout remains sealed.
