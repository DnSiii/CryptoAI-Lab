# V98 Independent BR — original pre-registered historical rejection (2026-10-24)

**Decision: REJECT_BR_HISTORICAL_GROWTH_OR_MARGINAL.** BR is permanently rejected under its original preregistered gates; it is not a validated champion, paper engine or live engine. No post-result signal, threshold, sign, window, gross, funding, friction, ablation or leverage rescue. The original architecture is preserved in [preregistration](br_preregistered_architecture_20261024.md).

## Original reproducible evidence

- GitHub Actions run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40087374629 at commit `70e2d86d55f56ad1a8432f9de475069ee303c670`.
- 5 original paths × 3 capitals × 3 fee tiers × 2 funding orderings = **90/90 physical training cells survived**. Ubuntu 22.04 and 24.04 reproduced all original receipts; 180/180 independent artifact arithmetic checks, zero errors.
- Separate native source/funding/intrabar audit independently reconstructed **65,088 hourly settlements** = 4 fee/order cases × 16,272 hours, including **81 intrabar corners** per hour, signed 8h funding and **9,144 authenticated source events**. Audit passed. These are physical/accounting checks, **not evidence of profitable alpha**.

## Full BR portfolio — USD10k, 2023/2024 historical TRAINING ONLY, carried-before-fill

| Costs | 2023 CAGR | 2024 CAGR | Two-year CAGR | Max drawdown | Turnover USD | Fees+slippage USD | Native funding USD | Fill hours |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Base | +23.077% | +14.887% | **+18.906%** | 23.936% | 825,097.06 | 825.10 | -127.40 | 119 |
| Severe | +14.978% | +0.181% | **+7.314%** | 26.630% | 773,183.94 | 3,865.92 | -87.41 | 121 |
| Supersevere | -21.441% | -55.414% | **-40.840%** | 69.233% | 545,671.11 | 8,185.07 | +8.67 | 127 |

With **new-after-fill** funding ordering, severe 2024 CAGR is **−3.606%**, failing the original full-portfolio annual growth gate.

## Full-minus-original-ablation annual log-growth (USD10k, carried-before-fill)

| Sleeve | 2023 base | 2024 base | 2023 severe | 2024 severe |
|---|---:|---:|---:|---:|
| Opportunity | −0.32053 | −0.05637 | −0.34709 | −0.01985 |
| Relative Value | +0.00014 | +0.36433 | +0.00888 | +0.34891 |
| Stress/Recovery | −0.02149 | −0.11220 | +0.01233 | −0.13768 |

All three **strict positive-marginal gates fail** over the required year/fee/order grid, even though Relative Value helped in some folds. It cannot be promoted as a standalone engine or used to rescue BR. Original core-only base CAGR was +68.48%, versus +18.91% for the complete engine; this is a diagnostic comparison, not a candidate selection.

## Mechanistic failure and immutable boundaries

The original full BR path incurred **US$825,097 base turnover** at US$10k initial capital, versus about US$210,411 for core-only; the three sleeves collectively imposed substantial friction and adverse path-dependent trading, despite lower funding outflow. This is a portfolio integration problem, not a missing accounting test. Next architecture must be structurally different, with **ex-ante sleeve contribution, lower inventory churn and true cost-adjusted compounding**, rather than modifying BR.

Only authenticated BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT Binance USD-M 1h Dec2022-Dec2024 Clean-4 training bytes were loaded. **2025 untouched**, 2026+ excluded, XRP quarantined, old Phase083 holdout ineligible. No V14/V15/V99 benchmarks/signals/parameters read. V16 Frozen, V99 Frozen, V99 branch/workflows/reports/paper untouched. No real trading.
