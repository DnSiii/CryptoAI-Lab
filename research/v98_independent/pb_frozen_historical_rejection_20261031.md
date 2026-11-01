# V98 PB — irrevocable frozen training rejection (2026-10-31)

**Binding decision: REJECT_PB_TRAINING; 26 economic gate failures.** No post-result changes to funding sign, lookback, threshold, weight, leverage, cost or gross. All PB signals and allocations remain exactly as preregistered in `pb_funding_dislocation_prereg_20261031.md`. This is **not** an approved engine, champion, paper PnL, live strategy, or future holdout result.

- Preregistration before economic run: `pb_funding_dislocation_prereg_20261031.md`.
- Initial workflow `41262841169`: mechanical failure because precommitted virtual gross 0.88 was passed to inherited physical planner whose default cap was 0.84; no complete-system economics in that attempt. Incident `pb_initial_execution_contract_incident_20261031.md`. A single code-only contract repair passed the preregistered 0.88 to PB-local unchanged physical settlement; **no strategy parameter changed**.
- Final physical workflow: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41262923414, SHA `ca183dda0d4b1c0ff7c15468aa842502d5616249`. All **30/30 physical cells completed** (five books, three cost tiers, two funding orders); 157 weekly decisions; 27,048 Clean-4 source hours and 13,524 native funding-rate events. Source year 2025 is **exposed training**, never unseen validation.
- Original immutable economic receipt: `pb_full_training_frozen_result_20261031.json`. Independent decision/allocator oracle: zero mismatches. Base carried-before-fill 26,303 hours cash-identity reconciled, zero mismatches; 193 fill events and fee/slippage/funding independent reconstruction, zero mismatches. These are accounting/causality checks, **not** out-of-sample predictive validation.

| Full portfolio, carried-before-fill | Base | Severe | Supersevere |
|---|---:|---:|---:|
| CAGR simulated | +14.73% | +8.54% | +2.29% |
| Max drawdown | -44.14% | -46.04% | -47.98% |
| Turnover (USD, initial 10k) | 1,582,034 | 1,447,599 | 1,319,465 |
| 2025 annual return | -8.51% | -13.19% | -17.92% |

Base optional sleeve full-minus-ablation log-growth: Opportunity **+0.01442** (below +0.02 binding threshold); Relative Value **-0.01006**; Stress/Recovery **-0.03258**. Severe: +0.01243, -0.01405, -0.03604. Risk and turnover gates also fail; 26 recorded gate failures in frozen JSON. This disproves the PB complete-system hypothesis under its own preregistered test; do not cosmetically rescue.

**Source/release restrictions:** exact exchange-origin 13,524 `markPrice` event objects are still unavailable because official `/fapi/v1/fundingRate` access returned HTTP 451 from Linux/macOS GitHub runners. The official hourly mark OHLC envelope used here is a conservative sensitivity bound, not exact tick settlement. Authorized original official HTTP JSON page export plus raw headers/URLs/timestamps/SHA256, independent chain-of-custody audit, untouched prospective chronological validation, final holdout, and only then external benchmark remain mandatory. No V16 Frozen, V99, V99 paper, XRP, 2026+, or contaminated Phase083 access.

**Next:** design a *new, economically distinct* complete seven-slot composition based on independent mechanism, not PB parameter rescue. The seven-system root-cause audit `v98_seven_frozen_systems_root_cause_20261031.md` shows sparse optional sleeve marginals are the recurring critical failure. Preserve all rejections and frozen evidence.
