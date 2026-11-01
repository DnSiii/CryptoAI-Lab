# V98 PH — permanently rejected after full physical training and independent audit (2026-11-01)

**Binding: REJECT_PH_TRAINING. No champion promoted. No paper/live.** PH funding-crowding seven-slot hypothesis is not approved; do not change its signs, thresholds, windows, weights, leverage, cost tiers, missing-OI policy or gates to rescue these results. This is exposed **2022-2025 training**, not untouched validation, not final holdout, and not actual trading.

## Immutable provenance
- [PH preregistration](ph_funding_crowding_composed_prereg_20261101.md) was committed at `ab51462ecb787dabcd4ca899da7bc7d8a94a77b7` **before** PH implementation or economic results.
- Executable + independent oracle + receipt auditor + dedicated workflow were committed before run at SHA `8e20cc8edc2418a0bfa7e1190a5174fa2fc667ba`.
- [Full 30-cell physical execution and separate audit](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41290537556), pinned to that SHA. Workflow conclusion **failure is deliberate enforcement of economic rejection**: the physical job succeeded and the separate audit independently reproduced all binding failures before the final rejection step.
- Sources: Clean-4 1h Dec-2022 through Dec-2025, 13,524 native funding events with conservative official hourly mark envelopes, 106,920 verified hourly asset OI records, 1,272 quarantined, 143/157 OI-eligible weekly decisions. All 2025 exposed training; no exact funding-event markPrice attestation. No XRP, 2026+, contaminated Phase083 holdout or external benchmarks accessed.

## Measured simulated complete-PH economics (carried-before-fill)
| Full PH | Base | Severe | Supersevere |
|---|---:|---:|---:|
| CAGR | +4.9371% | +0.0788% | -4.8920% |
| Max drawdown | -38.4682% | -40.5558% | -42.7189% |
| Turnover (initial USD10k) | USD1,106,623 | USD1,027,644 | USD950,682 |
| 2023 net return | +21.1181% | +15.4941% | +9.7321% |
| 2024 net return | -7.3681% | -11.9801% | -16.6781% |
| 2025 net return | +2.9986% | -1.3979% | -5.9101% |
| Positive days / 1,096 | 483 | 472 | 468 |

All **30/30 physical cells feasible**, 157 weekly decisions, 26,303 cash hours independently reconciled (0 mismatches), 190 net fill events independently reconstructed (0 mismatches), 157 x 5 independently reconstructed signal/allocation decisions (0 mismatches). The separate receipt auditor passed **60/60 arithmetic checks**, reproduced **26/26 binding economic failures** and rejected **4/4 tampered receipts**. No hidden claim of profit or completion.

### Optional sleeve marginal log growth (full minus leave-one-out)
| Sleeve | Base | Severe | Supersevere |
|---|---:|---:|---:|
| Opportunity | -0.032271 | -0.036829 | -0.041727 |
| Relative Value | +0.019937 | +0.009521 | -0.001803 |
| Stress/Recovery | +0.002545 | +0.001743 | +0.000878 |

Raw activations: Opportunity 18, Relative Value 31, Stress/Recovery 2; raw activation is not incremental profitability. Opportunity destroys capital; RV marginal fails the binding +0.02 threshold in both base and severe; Stress is too sparse and marginally negligible. Full CAGR, turnover and annual gates also fail. **No PH sleeve is promoted**, and neither the nearly-threshold RV nor any result may be cosmetically retuned or cherry-picked.

## Critical path
1. No complete seven-slot V98 internally approved. Next hypothesis must be economically distinct from PH's funding-crowding unwind and PG's OI stock-to-flow; avoid recycling these failed parameterizations. Target robust positive *marginal net log growth* of every optional sleeve with realistic turnover and tails.
2. Exact **13,524 exchange-origin funding-event markPrice** objects remain missing, with symbol/fundingTime/fundingRate/markPrice, raw HTTP bodies/headers, UTC chronology, pagination, SHA256 and verifiable authorized custody. The official Binance USD-M endpoint returned HTTP 451. Alternative: authorized exchange-origin export independently audited by the existing V98-only importer. The hourly mark envelope is not an exact tick.
3. Untouched prospective chronological validation/final holdout remain unavailable. The old Phase083 holdout is contaminated and 2025 exposed; do not access 2026+ while training. V14/V15/V99 remain unopened external benchmarks until V98 is internally frozen and independently validated.

Only `research/v98_independent/ph_*` and its dedicated `.github/workflows/v98-independent-ph-*` were created. V16/V99 Frozen, V99 research/workflows/reports, V99 paper and holdout untouched. No actual trades, no paper/live authorization.
