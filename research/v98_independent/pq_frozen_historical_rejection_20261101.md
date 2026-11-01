# V98 PQ — frozen exposed-history economic rejection (2026-11-01)

**Binding: REJECT_PQ_TRAINING permanently.** PQ downside/upside semivariance and volume-expansion architecture was preregistered in commit `e8c42375cb189eb511c1537a6bd0eccb20b9b896` before its implementation and before any PQ economic result. Physical run [41328067931](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41328067931) completed all 30 cells; its final red status is the intentional binding economic rejection gate, not an incomplete backtest. Frozen receipts: `pq_full_training_frozen_result_20261101.json` and `pq_frozen_independent_receipt_audit_20261101.json`. No parameter, sign, weight, threshold, funding order or gross can be altered to rescue PQ.

## Complete seven-slot simulated result — exposed training, not holdout

| PQ full portfolio | Base | Severe | Supersevere |
|---|---:|---:|---:|
| CAGR | +5.88% | +1.30% | -3.38% |
| Max drawdown | -48.67% | -50.39% | -52.16% |
| 2023 | -4.45% | -9.16% | -13.95% |
| 2024 | +4.25% | +0.22% | -3.93% |
| 2025 | +19.16% | +14.19% | +9.10% |
| Turnover from USD10k | USD939,895 | USD877,714 | USD817,006 |

The displayed funding order is carried-before-fill; new-after-fill differences were minor and independently included in the frozen 30 cells. 157 weekly decisions and 26,303 hourly cash reconciliations; native 13,524 funding events use conservative hourly worst-side mark envelopes, **not exact settlement event marks**. Base: 396 positive days, hourly NAV-change Profit Factor 1.0075 (NOT trade-level PF), max single-asset gross concentration 100%. Do not infer live profitability.

## Independent audit and diagnosis

The separate scalar signal/allocator oracle reproduced all 157 decisions and all five target books with **zero mismatches**. The independent ledger reconciled 26,303 hours with zero cash identity errors, maximum absolute arithmetic discrepancy 1.82e-12. The separate receipt auditor passed **60/60 arithmetic checks**, reproduced **20/20 economic gate failures** and rejected **4/4 tamper attempts**. Failure is economic, not source geometry or implementation.

PQ raw optional activations: Opportunity 15, Relative Value **0**, Stress/Recovery **0**. Base net log-growth Opportunity leave-one-out +0.01109 (below binding +0.02); severe +0.00583. RV and Stress marginal contributions both exactly zero. Severe CAGR +1.30% and 2023 negative, severe max drawdown -50.39%. The complete composed engine does not meet its preregistered gates. Do not rescue empty modules by relaxing thresholds after observing results.

## Next critical path

No complete V98 internally approved. A next genuinely distinct return mechanism should start with authenticated source economics (e.g. independently sourced spot/perpetual basis and executable two-leg costs) rather than another minor permutation of already failed semivariance, trend, premium, OI, funding polarity or BTC lead/lag. Do not open V14/V15/V99 for tuning.

The remaining **13,524 exchange-origin exact funding-event `markPrice`** values require authorized raw `/fapi/v1/fundingRate` pages, HTTP response Date and headers, original URL, UTC retrieval, per-page SHA256 and independently checked custody; prior direct requests returned HTTP 451. Binance Vision monthly funding-rate archives publish rates but not exact event mark prices, so they cannot replace that evidence. An authorized exchange-origin export with equivalent independently verified provenance is the alternative. Even with exact marks, a passing new V98 still needs separate chronological validation, genuinely untouched future holdout, post-freeze benchmarks and paper/live authorization. No 2026+ data or contaminated Phase083 holdout was used.

**Scope:** Only V98 Independent branch `research/v98-independent-zero` and V98 namespaced files/workflow. V16 Frozen, V99, other branches and paper untouched.
