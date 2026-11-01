# V98 PI — permanently rejected after physical training and independent audit (2026-11-01)

**Binding: REJECT_PI_TRAINING. No champion promoted, no paper/live.** This is exposed 2022–2025 training, **not** untouched validation or final holdout. PI is not to be reparameterized or cosmetically rescued after its results.

## Immutable provenance
- [PI architecture preregistration](pi_positioning_elasticity_prereg_20261101.md) was committed before code/economic results at `d927e8fd6e3b2f47fe8f57ffafabf5f8222ac215`.
- Executable, separate scalar oracle, independent receipt auditor and workflow were committed before the full historical run at `c06058dc56fd2f5e6c3bef50f131e17474d548ff`.
- [Physical 30-cell run and separate independent audit](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41294427826). Workflow's final failure is **deliberate enforcement of economic rejection**: physical and independent audit steps passed; the binding economic gate failed.
- [Full immutable receipt](pi_full_training_frozen_result_20261101.json) and [independent audit](pi_independent_audit_frozen_20261101.json) preserve numerical evidence. No external engine, 2026+ data or holdout used.
- Pinned Clean-4 native funding 13,524 events, 27,048 historical hours, 106,920 verified OI asset-hours, 1,272 quarantined OI asset-hours, 143/157 OI-eligible decisions; official hourly mark envelope is **not** exact funding-event markPrice.

## Complete PI simulated economics (carried-before-fill)

| PI full | Base | Severe | Supersevere |
| --- | ---: | ---: | ---: |
| CAGR | 8.4875% | 3.7825% | -1.0311% |
| Max drawdown | -39.3239% | -41.1930% | -43.1359% |
| Turnover (USD10k initial) | USD 1,061,507 | USD 989,125 | USD 918,603 |
| 2023 net return | 17.2181% | 11.9428% | 6.5790% |
| 2024 net return | -2.4090% | -6.7517% | -11.1998% |
| 2025 net return | 11.6243% | 7.0892% | 2.4253% |
| Positive days / 1096 | 449 | 444 | 438 |

All **30/30 physical cells feasible**. 157 weekly decisions, 26,303 cash hours independently reconciled (zero mismatches), 154 net fill events independently reconstructed (zero mismatches), 157 x 5 signal/allocation decisions (zero mismatches, max error 1.5439038936193583e-15). Independent receipt audit: **60/60 arithmetic checks**, **16/16 economic failures reproduced**, **4/4 tampered receipts rejected**.

### Optional sleeve full-minus-leave-one-out marginal net log growth

| Sleeve | Base | Severe |
| --- | ---: | ---: |
| Opportunity | 0.056481 | 0.053099 |
| Relative Value | -0.018097 | -0.020514 |
| Stress/Recovery | -0.001549 | -0.001816 |

Raw optional activations: Opportunity 10, RV 7, Stress 1. Opportunity had positive marginal growth **in this rejected complete PI experiment**, but does not independently pass a new architecture's gates and must not be transferred as a pre-approved sleeve. RV and Stress **destroyed** net wealth; both fail marginal gates. PI also failed base/severe CAGR, base turnover, and severe 2024 positive-year gate. The 16 failures include both funding execution orders. No retuning after inspection.

## Critical path, no cosmetic next phase
1. **No complete V98 approved.** Future hypothesis must be structurally distinct from PH funding crowding, PG OI stock/quote flow and PI OI-price elasticity. Require complete-system net compounded wealth, robust marginal optional contributions and independent accounting; no sign/threshold rescue.
2. **Exact 13,524 exchange-origin funding-event markPrice records missing.** Require symbol, fundingTime, fundingRate, markPrice, raw response/request headers and bodies, UTC pagination, SHA256 and verifiable authorized custody. Official Binance USD-M historical endpoint returned HTTP 451. Authorized exchange-origin export independently audited by V98-only importer is the alternative; hourly mark envelope is not an exact event tick.
3. Untouched prospective validation/final holdout unavailable; 2025 is exposed training. Phase083 holdout contaminated. V14/V15/V99 remain unopened external benchmarks until an internally frozen V98 passes independent validation.

All new files restricted to `research/v98_independent/pi_*` and dedicated `.github/workflows/v98-independent-pi-*`. V16/V99 Frozen, V99 branch/workflows/reports/paper and holdout unchanged. No live or paper authorization.
