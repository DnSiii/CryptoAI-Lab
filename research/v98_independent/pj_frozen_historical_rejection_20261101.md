# V98 PJ — binding frozen seven-slot training rejection (2026-11-01)

**Decision: REJECT_PJ_TRAINING permanently. No champion, paper or live authorization.** This is exposed 2022–2025 training only; 2025 is not validation. No sign, threshold, weight, gross or cost rescue of PJ.

## Pre-result provenance and reproducible evidence
- [Binding architecture preregistration](pj_channel_propagation_prereg_20261101.md), committed before implementation at `b8807a4363ce5c7be78c460bad08649fbcc21b56`.
- [Physical 30-cell execution and independent audit](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41298964183), executable commit `dfcaac22859229f3b1a80dcb28a7aa55d7b8d5f9`. The first run `41298924023` stopped at a synthetic **future funding fixture** mask error before any PnL; the correction changed the synthetic fixture only, not strategy signals/weights, cost tiers, or preregistration. The final workflow's nonzero status is deliberate enforcement of economic rejection after 30 physical cells and audit passed.
- [Full frozen historical receipt](pj_full_training_frozen_result_20261101.json); [separate independent audit](pj_independent_audit_frozen_20261101.json). 27,048 hours, 13,524 native funding events, 157 weekly decisions; no 2026+, Phase083 holdout or external benchmark opened.

## Measured full-system economics (carried-before-fill, USD10k initial)
| Metric | Base | Severe | Supersevere |
|---|---:|---:|---:|
| CAGR | **-2.6660%** | **-3.0044%** | **-3.3660%** |
| Maximum drawdown | -9.5716% | -10.3871% | -11.2533% |
| Turnover | USD72,142 | USD71,798 | USD71,431 |
| 2023 return | 0.0000% | 0.0000% | 0.0000% |
| 2024 return | -2.9692% | -3.5184% | -4.1038% |
| 2025 return | -4.9666% | -5.4193% | -5.9025% |
| Positive days / 1096 | 52 | 50 | 48 |

Both funding execution orders yielded the same measured outcomes for PJ. All **30/30 physical cells feasible**; 157 decisions x five books independently checked, zero mismatches; 26,303 cash hours independently reconciled, zero mismatches; 28 net fill events independently reconstructed, zero fee/slippage/funding mismatches. Separate receipt audit: **60/60 arithmetic checks, 18/18 preregistered economic failures reproduced, 4/4 tampered receipts rejected**.

### Optional sleeves destroy growth; no recovery of PJ
Raw Opportunity activations **1/157**, Relative Value **12/157**, Stress/Recovery **0/157**. Net full-minus-leave-one-out log growth:
| Sleeve | Base | Severe | Supersevere |
|---|---:|---:|---:|
| Opportunity | -0.017261 | -0.017912 | -0.018610 |
| Relative Value | -0.025334 | -0.033966 | -0.043221 |
| Stress/Recovery | 0.000000 | 0.000000 | 0.000000 |

All three optional sleeves fail binding positive-marginal gates. Full portfolio underperforms core-only even in base; 2023 zero return indicates inactive system, not positive edge. The low drawdown reflects inactivity and **is not** success. Do not repurpose the rejected PJ configuration as a champion.

## Remaining delivery path
1. A genuinely distinct economic architecture and source of compounding are required. Repeatedly recombining channel/price proxies with no incremental economic contribution is not a productive path. No complete V98 has passed internal gates.
2. **13,524 exact Binance exchange-origin funding-event markPrice objects** still missing: symbol, fundingTime, fundingRate, markPrice, original request and response body/headers, UTC pagination, SHA256 and authorized origin/custody evidence. The direct historical USD-M endpoint returned HTTP 451. Alternative: independently audited authorized raw exchange-origin export. The official hourly mark envelope is not an exact tick.
3. Independent untouched prospective validation and final holdout remain absent; 2025 already exposed and old Phase083 contaminated. External V14/V15/V99 benchmarks remain unopened until an independently validated complete V98 is frozen.

All new/changed files are PJ namespaced under `research/v98_independent/` or its dedicated PJ workflow; no V16/V99 Frozen, V99 research, V99 paper, other branches or holdout changed.
