# V98 Independent DE — immutable historical rejection and capital-neutral mechanism audit (2026-10-25)

**Decision: REJECT_DE_HISTORICAL_GROWTH_OR_MARGINAL.** DE is permanently rejected as a complete seven-slot trading engine. Do not retune its signs, windows, budgets, router, gates, physical governor or source to rescue it. Historical 2023-2024 TRAINING only; no 2025 holdout, 2026+, XRP, external benchmark, paper or live orders.

## Chronology and real execution
- Pre-result complete seven-slot preregistration commit `6f7685e8fbc5506b8101f4bfeea7c485064feb71`, before DE source code `313d5cef4208b2ea572d0eb2429893a4c08e26a2`.
- Original real-run blockers: CLI typo `ade_argument` and settlement key `hideen_borrow` accidentally introduced during file namespacing. Corrected **without any strategy or gate change** in commits `da32c3c2184449b0392db9a3ed8f0ca74a8f7adf` and `d7a1a316c16ebfa924af376938f16dfbe982d5ea`.
- Authenticated pinned Clean-4 native 2022-2024 run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40163324783 .
- Independent artifact-only native price/funding/cost audit: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40163433046 .
- Causal future perturbation PASS; source viability PASS. 2023/2024 effective epochs: Core 54/57, Opportunity 15/12, RV 28/22, Stress 28/28.
- Five paths x base/severe x two funding orderings = **20/20 physical cells survived**, Ubuntu 22.04/24.04 reproduced, independent cross-OS audit errors=[]; not an independent event-by-event ledger replay.

## Historical complete-engine results, USD10k, carried-before-fill
| Metric | Base | Severe |
|---|---:|---:|
| Two-year CAGR | +39.3270% | +23.9435% |
| 2023 net return | +98.9833% | +78.5408% |
| 2024 net return | **-2.3997%** | **-13.9328%** |
| Max drawdown | 26.1003% | 28.3752% |
| Hourly net PF | 1.03405 | 1.02215 |
| Hourly payoff | 0.96807 | 0.96088 |
| Hourly win rate | 51.6479% | 51.5449% |
| Positive UTC days | 32.1477% | 29.6854% |
| Peak gross/NAV | 0.77601 | 0.77096 |
| Native signed funding | -$1,115.45 | -$944.95 |
| Core-only CAGR | +37.6014% | +21.9975% |
| Full-minus-core final NAV | +$478.41 | +$479.09 |

## Independent net-log-growth ablations, full-minus-sleeve
| Sleeve | 2023 base | 2024 base | 2023 severe | 2024 severe | Decision |
|---|---:|---:|---:|---:|---|
| Opportunity | -0.0042314 | +0.0018046 | -0.0050542 | +0.0025619 | FAIL (2023) |
| Relative Value | **+0.0177848** | **+0.0031798** | **+0.0188801** | **+0.0035021** | PASS (both funding orders, both years) |
| Stress/Recovery | +0.0030031 | -0.0008376 | +0.0046337 | +0.0033103 | FAIL (2024 base carried; also new-after-fill) |

**Important but non-promotable research observation:** a capital-neutral within-core relative tilt achieved positive counterfactual contribution in both chronological training years, both fee scenarios and both funding orders. This is **not** a frozen independent alpha or an approved component: the complete DE architecture failed full annual growth, minimum CAGR and two other marginal gates. The 2024 RV contribution is small and could be noise. No selection or cherry-picked promotion from this rejected architecture.

## Independent path-level native decomposition, USD10k base
- Full minus core-only: **+$478.41** final NAV = +$408.63 price/interaction +$64.60 signed funding - (-$5.17 extra fees/slippage).
- Full minus no-RV: **+$402.91** final NAV = +$428.51 price/interaction -$9.32 funding -$16.28 extra fees/slippage.
- Full minus no-Stress: **+$42.01** final NAV = -$55.15 price/interaction +$65.19 funding - (-$31.97 extra fees/slippage).
- Full minus no-Opportunity: **-$47.19** final NAV = -$58.07 price/interaction +$16.52 funding -$5.64 extra fees/slippage.
- Exact cash-ledger identity asserted to USD1e-6 in independent artifact-only audit. This is path-level, not event-by-event replay.

**Critical path:** next candidate must be a genuinely new complete high-growth architecture, not a DE/DD rescue. Capital-neutral overlays are a distinct economic mechanism worth researching, but do not copy DE rejected signals/parameters or tune to DE returns. Prioritize raising the full system's *2024* net growth and independent causal/event-level audit before opening 2025. Preserve all frozen engines and paper. No real trading.
