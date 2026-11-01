# V98 PS — permanently frozen historical rejection (2026-11-01)

**Decision: REJECT_PS_TRAINING. NOT a validated V98 engine.** Preregistration committed at `7a4dfb19a9f9c7575975bc9edd2b51936230c0f2` before implementation and PS historical PnL. Technical pre-PnL ledger-clock correction at `3baf45535d18fe8331d5dde798f517c3e44679d9`: the shared physical runner records 26,303 hours from hour 745 even though PS signals start at hour 1008. The correction did not change any economic gate. Full GitHub Actions execution: [41348463476](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41348463476). The workflow's final failure is the **intentional binding economic rejection**, not a physical or independent accounting failure.

## Exposed 2023–2025 TRAINING ONLY, simulated, no holdout

| PS full carried-before-fill | Base | Severe | Supersevere |
|---|---:|---:|---:|
| CAGR | +14.8733% | +2.6698% | -8.9380% |
| Maximum drawdown | -40.2949% | -48.5738% | -56.1413% |
| 2023 | +60.4106% | +42.9511% | +26.3415% |
| 2024 | -11.6360% | -21.0140% | -29.9664% |
| 2025 | +6.9524% | -4.1486% | -14.6643% |
| Turnover USD, USD10k initial | 3,019,230 | 2,538,659 | 2,130,309 |
| Fees + slippage USD | 1,811.54 | 5,077.32 | 7,456.08 |
| Native funding cash USD | -876.57 | -758.78 | -654.02 |

**30/30 physical cells passed execution**, 1,085 causal daily decisions, 1,063 net fill hours in base, 21 forced safety fill hours, 26,303 independent hourly cash/funding/fill reconciliations with zero mismatches. The independent signal+allocator oracle had zero mismatches across 1,085 decisions and five books. Receipt audit independently reproduced **60/60 arithmetic checks**, all **26 binding economic gate failures** and rejected **4/4 tamper cases**. Immutable source/decision evidence: `ps_full_training_frozen_result_20261101.json`, `ps_frozen_independent_receipt_audit_20261101.json`.

## Why PS failed and what must not be rescued

Daily inventory generated very high turnover and cost drag. In the base full portfolio, 1,063 fill hours on 1,085 daily decisions (includes 21 safety interventions) and USD3.019m turnover from USD10k initial equity; this violates the preregistered USD1m base/severe ceiling. CAGR is below both base 80% and severe 60% hurdles; severe DD -48.57% breaches -45%; severe 2024 and 2025 annual returns are negative.

Base optional leave-one-out marginal log growth: Opportunity **+0.10462**, Relative Value **+0.01856** (<.02), Stress/Recovery **-0.04400**. Severe: Opportunity **+0.04345**, Relative Value **+0.00957** (<.02), Stress/Recovery **-0.05156**. Opportunity fails the separate 2025 annual marginal floor; Stress/Recovery additionally fails the severe 2025 annual marginal floor. All 26 violations reproduced for both funding orders. Opportunity's positive aggregate marginal is **not** approval of PS or permission to copy it into a new architecture without fresh preregistration and independence.

**No PS sign, weight, lookback, entry threshold, cost, turnover or leverage change after exposure is permitted. PS is permanently rejected.** In particular, reducing PS turnover after inspecting PS returns would be a prohibited cosmetic rescue. A new architecture must present a distinct source of expected net growth and precommitted execution economics rather than another daily variant of this rejected system.

## Remaining critical-path blockers

No V98 complete engine passes. Native funding rates are authenticated, but the **13,524 exchange-origin exact funding-event `markPrice` values** remain missing due historical HTTP 451; an authorized Binance-origin raw fundingRate export with original URLs, response bytes, Date headers, UTC capture, per-page SHA256 and independently verified custody is required, or equivalent authorized exchange-origin attestation. The 1h worst-side mark envelope is exploratory, not exact settlement. Account-specific historical fees and executable bid/ask/depth/impact also remain unverified. Separate chronological validation and genuinely untouched future holdout are still required before a frozen candidate may be benchmarked externally; no 2026+ used in training, no XRP, Phase083 or V14/V15/V99 tuning. V16/V99 Frozen, V99 branch/workflows/reports/paper unchanged. No real or paper trading authorized.
