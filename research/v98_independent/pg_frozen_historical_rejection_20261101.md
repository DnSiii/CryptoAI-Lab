# V98 PG — frozen independent full-history rejection (2026-11-01)

**Binding decision: REJECT_PG_TRAINING permanently. No champion promoted, no paper/live.** Do not alter PG signs, thresholds, windows, weights, leverage, funding, cost tiers or missing-window policy after these results. This is a complete seven-slot simulated *exposed training* result, **not** validation, actual trading PnL, or a successful engine.

## Precommitted design and source
- [PG preregistration](pg_inventory_stockflow_composed_prereg_20261101.md) was committed at SHA 7bb4239b9358bc4c58ec69130b018a5355016133 **before** executable implementation or any PG PnL.
- [Full 30-cell physical execution and separate independent audit](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41286283927) used pinned executable SHA feaf02e030926fd194e38ed466c7e08d757c2dba. Workflow failure is **intentional economic rejection** after successful audit, not missing source/runtime.
- Authenticated Clean-4 BTC/ETH/BNB/SOL 1h 2022-12 through 2025-12, signed native funding, conservative official hourly mark envelope. Native OI sources independently audited: 106,920 verified hourly-asset records, 1,272 quarantined; 143/157 weekly OI-eligible decisions. 2025 was already exposed training, not independent validation. **No exact funding-event markPrice attestation**.
- Full source, signal, allocator and book oracle: 157 decisions x 5 books, **0 mismatches**, max reported error 0. Native OI optional sleeve raw activations: Opportunity 66, RV 59, Stress/Recovery 32 decisions; activation does not prove profitability.

## Actual simulated 30-cell economics (carried-before-fill)
| Full PG | Base | Severe | Supersevere |
|---|---:|---:|---:|
| CAGR | **+12.10%** | **+6.64%** | **+0.97%** |
| Maximum drawdown | -30.18% | -34.53% | -40.27% |
| Turnover (initial USD10k) | USD1,423,781 | USD1,312,907 | USD1,204,541 |
| 2025 net return | -6.00% | -10.75% | -15.72% |
| Positive days / 1,096 | 527 | 521 | 514 |

All **30/30 physical cells passed**. Independent cash reconciliation: 26,303 hours, zero mismatches; independent fee/slippage/funding reconstruction: 228 net fill events, zero mismatches. **Separate-run arithmetic and economic gate audit:** 60/60 arithmetic checks, all **18/18 binding economic failures reproduced**, four tampered receipts correctly rejected. [Full frozen result](pg_full_training_frozen_result_20261101.json); [independent frozen audit](pg_independent_audit_frozen_20261101.json).

### Marginal contribution to complete PG (net log growth, full minus leave-one-out)
| Optional sleeve | Base | Severe | Supersevere |
|---|---:|---:|---:|
| Opportunity | +0.03391 | +0.02543 | +0.01476 |
| Relative Value | +0.00167 | -0.00467 | -0.01508 |
| Stress/Recovery | -0.04837 | -0.04821 | -0.04812 |

Opportunity had a positive marginal in the full PG under base and severe, but **PG is rejected**: this is not a module approval, permission to salvage the failed candidate, or justification to reuse its parameters. RV failed the required +0.02 marginal and Stress destroyed growth. Both funding orders failed CAGR and turnover limits in base and severe; severe also failed positive-year gate (2025 -10.75%). Core alone is not an approved seven-slot engine.

## Honest critical path
1. **No complete seven-slot V98 has passed the internal economic gates.** A next research hypothesis must be genuinely structurally distinct, particularly in RV/stress and in how optional sleeves earn incremental capital; no PG retuning or retroactive acceptance. Avoid making repeated OHLCV/OI proxies look like independent alphas.
2. The **13,524 exact native funding event objects** remain missing, specifically official symbol, fundingTime, fundingRate and event-tick markPrice, original HTTP request/response page bodies and headers, pagination and UTC chronology, SHA256 and independently verified lawful exchange-origin custody. Hosted Binance USD-M endpoint returned HTTP 451. Acceptable alternative: authorized exchange-origin export with verifiable custody, audited by existing V98-only importer and independent capture audit. Hourly mark envelopes are conservative approximations, not exact tick settlement.
3. A genuinely untouched prospective chronological validation/final holdout is still absent; 2025 is exposed training and old Phase083 holdout is contaminated. No 2026+ access in this research. V14/V15/V99 remain external benchmarks **not opened** until a complete V98 is frozen and independently validated.

Only V98 Independent namespaced files and its dedicated workflow were changed. V16/V99 Frozen, V99 research, V99 paper, contaminated holdout and external benchmarks were untouched. No actual trades or paper authorization.
