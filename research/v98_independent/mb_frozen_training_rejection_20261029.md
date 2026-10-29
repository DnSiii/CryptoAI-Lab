# V98 MB — terminal source-pass / economic-rejection receipt (2026-10-29)

**FROZEN REJECTION. Do not retune, transplant modules, use 2025 validation, holdout, benchmarks, or paper.** The complete seven-slot MB hypothesis was preregistered in commit `eaa5e629d356bf81282aacece1fef0f9d963f0c1` before code, source checks and PnL. New architecture used a causal atomic pre-fill allocator and a fixed ex-ante signed-funding loss reserve; actual future funding rates and mark OHLC were used only in ex-post conservative accounting, not sizing.

## Authenticated source gate — PASS
[Original run 40943533214](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40943533214): SHA-pinned Clean-4, 18,288 hourly bars/asset, 9,144 native signed funding events, 2022-12 warmup + 2023-24 TRAINING ONLY. Independent calendar replay mismatch **0**, invalid entries **0**, silent updates **0**, synthetic and authenticated future-mutation causality PASS, intended gross max 0.90 NAV. 2023 activations Opportunity/RV/Stress **18/10/16**; 2024 **16/8/20**; all >=8/year.

## Full-hour physical 30-cell training — ECONOMIC REJECT
[Original run 40943769825](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40943769825) executed all 30 physical cells: five books x three cost tiers x two signed funding settlement orders. The CI exit code 2 denotes **economic rejection**, not a runtime error. Artifact `12928775735` preserves the JSON. All 30 cells completed without physical fail-closed exceptions; atomic planner tests [40943648697](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40943648697) passed. Independent read-only receipt arithmetic [40943931702](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40943931702) verified **30/30 cells**, **zero arithmetic mismatches**, but is NOT an independent all-hour PnL oracle.

| Full MB, 2023-24 training only | Base | Severe | Supersevere |
| --- | ---: | ---: | ---: |
| CAGR | **+46.0091% FAIL** | +42.1039% | +38.0282% |
| Turnover / USD10k initial | USD574,880.86 | USD557,547.92 | USD539,654.04 |
| Max drawdown | -26.0748% | -27.2148% | -28.4192% |
| 2023 return | +70.9015% | +66.8079% | +62.5249% |
| 2024 return | +24.8070% | +21.1168% | +17.2755% |
| Opportunity marginal net log growth | **+0.019491 FAIL** | **+0.009736 FAIL** | -0.000735 |
| Relative Value marginal net log growth | **-0.027640 FAIL** | **-0.035338 FAIL** | -0.043608 |
| Stress/Recovery marginal net log growth | +0.069736 | +0.062338 | +0.054398 |

Fourteen original preregistered failures across two funding orderings: base CAGR <=50%; Opportunity marginal <=+0.02 base/severe; Relative Value marginal <=+0.02 base/severe and negative annual 2023 marginal. Turnover, severe drawdown and annual returns passed. **Do not optimize MB post hoc or reclassify the result.**

## Independent physical limitation and next economic hypothesis
No independent all-hour ledger/PnL oracle, exact funding-tick mark (HTTP 451; signed worst official 1h OHLC interval used instead), cross-OS, 81-corner reproducibility, separate 2025 validation or pristine future holdout was performed for MB because it failed the economic training gate. Fees/slippage are modeled assumptions, not actual account receipts. This is multiply selected historical TRAINING PnL, not a future performance estimate.

**Mechanistic finding:** after pretrade leverage and signed-funding causality were enforced, Relative Value remained a **negative marginal contribution** despite profitable Stress/Recovery; core opportunity cost remains the critical economic bottleneck. A new architecture must change the ex-ante joint capital economics, not merely decrease trading cost or reuse the best-looking MB sleeve. Do not access V14/V15/V99 signals, Frozen, 2025+, XRP, contaminated Phase083, or paper.

**Decision: REJECT_EARLY_TRAINING, permanently frozen.** No V98 complete candidate approved, no live authorization.
