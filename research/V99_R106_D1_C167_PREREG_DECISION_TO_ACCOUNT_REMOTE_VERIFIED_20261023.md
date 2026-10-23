# V99 R106 D1 C167 — exact preregistered decision-to-account binding (2026-10-23 BRT)

**Decision: DATA_ONLY/HOLD — NO PROMOTION.** This is source-only model integration, NOT authenticated historical economics. C1/C2 and archived candidates remain rejected. No validation, holdout, paper publication, orders, or Frozen/champion changes.

## Concrete gap closed

C165 independently reconciled modeled account cash, fees and funding, but accepted caller-supplied `Decision` objects as long as they were structurally causal. That left a posthoc signal-selection loophole: a coherent ledger with a cash-only override could pass accounting without being the single preregistered D1 rule. C167 now recomputes the **original D1/C136 fee-bound decision** at every supplied decision time from 168 previous paired spot/perp hourly opens, three already-settled funding fixes per asset and the known-at-t-1 native tier. It rejects mismatches *before* invoking the existing independent C165 two-scenario account replay.

C167 additionally binds every one of those 168 feature opens to the source journal's previous hourly marks, every funding fix to the preceding journal funding rows, and every causal tier to the fee schedule used for C140 accounting. Exact scenario decisions must match `fee_bound_intent`, not merely satisfy a necessary eligibility ceiling. This does **not** authenticate externally supplied data or receipts.

## Remote execution and independent verification

- Starting branch HEAD `44a6a24107f41a0696ab67b637e14ecbf038ac60`; additive C167 commit `3a7936ea54946cf5e9d03cd081df9e897eb35aee`.
- `compare_commits` independently confirmed **exactly three added paths, zero existing-file edits**: `research/verification/independent_d1_c167_preregistered_account_binding.py`, `research/tests/test_v99_r106_d1_c167_preregistered_account_binding.py`, and `.github/workflows/v99-r106-d1-c167-prereg-account-binding.yml`.
- Actual push-triggered GitHub Actions **40013962014**, job **120621130409**, completed **success** on 2026-10-23 19:46 UTC. Job logs show **66/66 pytest + 57/57 unittest = 123/123 tests**, including eight new C167 adversarial checks. The economic permission assertion also passed.
- The new 216h synthetic integration exercises **two** daily decision hours, **four** scenario-specific decisions, **672** feature asset-hour identities, and **12** settled-funding-fix identities. An intentionally artificial 0.3%/8h funding regime produces **two positive asset-pair decisions in severe, zero in supersevere**, with separate independently reconciled account ledgers. This rate is a TEST FIXTURE, not an OKX observation or profit estimate.
- Negative controls reject a posthoc cash override, fabricated historical feature open, forged settled funding, mismatched fee tier, missing decision day, wrong cost-path decision, and broken journal accounting.

## Remaining scientific blockers and next action

The C167 sample is **216h synthetic**, not the required 15,864h four-leg exchange history or the independent full-TRAIN economic trial. It does not replace missing original C141–C147/C152 local source modules; do not claim those were restored. Although C160/C161/C162 have separate 15,864h structural regressions, those tests are also synthetic and do not establish a real market edge.

Before one preregistered D1 complete TRAIN trial can be scientifically scored, obtain independently verifiable 2021–2023 paired BTC/ETH spot+perp first-party market history, historical as-of lot/contract terms, account-specific fee tier evidence, actual settled funding cashflows and real execution/slippage evidence. Contemporary 2026 OKX receipts must remain quarantined and cannot be backdated. After source binding, run both severe/supersevere paths, five chronological folds, 3x2 regimes, tail/drawdown and benchmark gates with independent re-execution; reject failed gates. Freeze a genuinely passing TRAIN candidate before sealed validation [2023-10-01,2024-01-18); final holdout >=2024-01-18 only by formal gates.

**No historical ROI, no paper PnL, no live order, no model promotion.**
