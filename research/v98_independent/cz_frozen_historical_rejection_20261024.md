# V98 Independent CZ — frozen historical rejection (2026-10-24)

**Decision: REJECT_CZ_HISTORICAL_MARGINAL.** CZ is permanently rejected as a *complete* seven-slot engine despite high historical training CAGR. No post-result changes to CZ signs, windows, budgets, thresholds, allocation scales, gross or gates. No candidate promotion, holdout access, benchmark or paper/live.

## Ex-ante and evidence
- Frozen preregistration commit `d808c0ab12ab5e9ac123e2925bcf913ffc5fad24` preceded CZ implementation and all CZ training PnL.
- First source run `40156069004` failed solely due to a mistaken workflow receipt filename `policz` introduced by template replacement. Corrected only the workflow receipt filename before source/PnL; successful official run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40156106166 .
- Authenticated Clean-4 BTC/ETH/BNB/SOL 1h 2022-12 warmup through 2024-12, native signed funding and conservative mark; 2025 sealed, 2026+ excluded, XRP quarantined, V14/V15/V99 unused.
- Source static future-perturbation PASS. Effective source epochs 2023/2024: Growth 14/14; Opportunity 12/15; Relative Value 37/36; Stress 17/19. All source gates passed.
- Five full/ablation paths x USD10k x base/severe x two funding orders = **20/20 unique physical cells survived**, reproduced Ubuntu 22.04/24.04, artifact-only audit errors=[]; this is **not** independent event-level replay.
- Independent artifact-only marginal diagnosis: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40156217049 .

## Full historical training portfolio, carried-before-fill
| Metric | Base | Severe |
| --- | ---: | ---: |
| Two-year CAGR | +84.0134% | +71.6310% |
| 2023 net return | +148.6247% | +131.7042% |
| 2024 net return | +36.3067% | +27.2269% |
| Max drawdown | 31.9093% | 31.7064% |
| Hourly net Profit Factor | 1.05477 | 1.04902 |
| Hourly net payoff | 1.03727 | 1.03292 |
| Hourly net win rate | 50.418% | 50.387% |
| Positive UTC days | 46.512% | 45.417% |
| Peak gross/NAV | 0.78316 | 0.77852 |
| Peak single-asset gross concentration | 100% | 100% |
| Signed native funding cashflow (USD10k start) | -$2,613.07 | -$2,359.15 |
| Fees | $325.11 | $1,183.20 |
| Slippage | $325.11 | $1,774.80 |
| Turnover | $650,229.77 | $591,598.42 |
| Physical fill hours | 103 | 103 |

## Full-minus-ablation marginal annual log growth (NOT CAGR)
`carried_before_fill`; other native funding order confirms the same gate failures.

| Sleeve | 2023 base | 2024 base | 2023 severe | 2024 severe | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Opportunity | -0.01807575 | -0.00691496 | -0.02172845 | -0.01042191 | FAIL both years |
| Relative Value | +0.00393647 | -0.13185785 | -0.01081049 | -0.13925598 | FAIL |
| Stress/Recovery | -0.06676496 | +0.04258840 | -0.07477121 | +0.04275890 | FAIL |

**Interpretation:** high system training CAGR is insufficient: all three satellites fail preregistered annual marginal gates, and single-asset concentration can reach 100%. No honest superiority or robust out-of-sample claim follows. CZ cannot be scaled or evaluated on 2025. Do not reinterpret positive core or annual portfolio PnL as passing complete-engine gates.

**Critical path:** a genuinely new, preregistered composed engine must add incremental net log wealth from independent sleeves without relying on an unvalidated high-beta core. Distinguish structural economic failure from workflow bugs; do not rescue rejected CZ. Before promotion require independent event-level replay, capacity USD1m/USD10m, supersevere costs, regime/tails/concentration and separate untouched 2025 validation. Frozen and V99 paper untouched. No real orders authorized.
