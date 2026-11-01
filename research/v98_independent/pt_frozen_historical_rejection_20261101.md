# V98 PT — permanently frozen historical rejection (2026-11-01)

**Decision: REJECT_PT_TRAINING. Not a validated V98 engine.** PT preregistered in commit `369e45c595be1f49162afad7d862acda5084219b` before implementation, source use and PT historical PnL. Distinct market-beta residual/liquidity hypothesis, not a modification of rejected PS/PR. Binding complete physical training and independent gate executed in GitHub Actions [run 41354259592](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41354259592). The final workflow failure is the **intended economic rejection**, not an unhandled run failure.

## Exposed 2023–2025 training, no holdout, simulated only

| PT full, carried-before-fill | Base | Severe | Supersevere |
|---|---:|---:|---:|
| CAGR | +7.3594% | +3.8342% | +0.1609% |
| Maximum drawdown | -39.6924% | -41.8283% | -44.4307% |
| 2023 return | +29.0445% | +25.2508% | +21.3030% |
| 2024 return | -10.5444% | -14.0030% | -17.5680% |
| 2025 return | +7.1999% | +3.9366% | +0.4910% |
| Turnover USD (USD10k initial) | 786,616 | 747,211 | 707,721 |
| Fees + slippage USD | 471.97 | 1,494.42 | 2,477.02 |
| Native funding cash USD | -921.74 | -889.26 | -856.17 |

**Physical:** all 30/30 scenario cells executed and passed solvency/source gates, 157 causal weekly decisions, 163 net fill hours and six forced safety fill hours in base full, 26,303 hourly accounting/fill/funding checks independently reconciled with zero mismatches. Independent scalar signal/allocator oracle had **zero mismatches across 157 decisions and five books** (max weight difference 1.39e-17). Independent receipt replay verified **60/60 arithmetic checks**, reproduced **all 26 binding economic failures** and rejected **4/4 tampering controls**. Receipt files: `pt_full_training_frozen_result_20261101.json` and `pt_frozen_independent_receipt_audit_20261101.json`.

## Falsification and no rescue

PT did **not** meet base CAGR >80% or severe CAGR >60%; severe 2024 annual return was negative. Its optional sleeves did not deliver the required independent marginal growth. Base leave-one-out marginal log growth: Opportunity **-0.01855**, Relative Value **-0.05301**, Stress/Recovery **+0.00424** (below binding +0.02). Severe: Opportunity **-0.02595**, Relative Value **-0.05462**, Stress/Recovery **+0.00397**. Opportunity 2025 and Relative Value 2023 annual marginal tests also failed. Even the PT core-only base CAGR was only **+10.1654%**, not a plausible complete-system champion. The core's BTC/alt residual structure and negative funding cash are descriptive causes, not a basis for post-result threshold/sign/weight/cost rescue. All 26 failures were reproduced under both funding orders.

The severe full-portfolio max drawdown (-41.83%) was within its -45% gate and turnover was below USD1m, but **survival alone does not establish growth**. Base 547/1096 positive days, 1% daily CVaR -6.40%, hourly net PF 1.0083, hourly payoff 0.9921 and hourly net win rate 50.40%; these are **hourly NAV** statistics, not trade-level PF/payoff/win rate. Peak single-asset gross concentration reached 100%, requiring continued concentration safeguards.

**PT is permanently rejected; no sign, beta window, liquidity threshold, weights, sleeve direction, leverage, costs or gates may be changed to rescue it.** A next hypothesis must be a genuinely different source of net compounded growth, with fresh pre-PnL preregistration. PT, PS, PR and other rejected engines are not champion candidates.

## Exact external blockers to final V98 delivery

- 13,524 missing **exchange-origin exact funding-event `markPrice` values**, blocked by prior historical Binance API HTTP 451. Obtain authorized raw `/fapi/v1/fundingRate` response pages with request URLs, original response bytes/HTTP Date headers, UTC capture times, per-page SHA256 and independent custody verification, or equivalent authorized exchange-origin export. The hourly worst-side envelope used here is an exploratory conservative proxy, not exact settlement.
- Historical account-specific fee tier and discounts, executable bid/ask/depth/market impact, liquidation/collateral evidence for intended capacity remain unverified. Public fee schedules do not attest historical fills.
- No complete V98 has passed exposed chronological training gates, so separate validation, genuinely untouched future holdout and prospective independent paper evidence are not yet eligible. No 2026+ training access, XRP, Phase083, V14/V15/V99 tuning, V16/V99 Frozen or V99 paper modification. No real/paper trading authorized.

All code, preregistration, frozen receipts and workflow are PT/V98 Independent namespaced only.
