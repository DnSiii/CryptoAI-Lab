# V98 Independent C1 — authenticated Clean-4 economic disposition (2026-11-12)

Source: [successful GitHub Actions run 43293372606](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/43293372606), branch `research/v98-independent-zero`, commit `1827f9a0947842d9739c8c3df8936292d0b1d733`, artifact `13977743163` (SHA256 `4bef5acff57e8b9b2a20275da6514ebc2db65d30255e1f2cb051bd3b7a2d81f7`). Results extracted from the successful authenticated job's stdout; the complete ledger is retained in the run artifact, not reproduced here. No 2026+ training or holdout accessed according to the runner output.

The same 27,048-hour Clean-4 history and native funding manifests were used for C1 and B0. Starting equity: 10,000. **Training-only research, not independent validation.**

| Cost scale | C1 final equity | B0 final equity | C1 minus B0 | C1 max drawdown |
| --- | ---: | ---: | ---: | ---: |
| 1x | 15,268.8076 | 14,562.0085 | +706.7991 | 22.0513% |
| 2x | 14,350.8512 | 14,263.1573 | +87.6939 | 22.1079% |
| 4x | 13,452.7261 | 12,762.2273 | +690.4987 | 22.3800% |

C1 independent arithmetic reconciliation returned maximum residual zero in each scenario. C1 UTC annual returns including warmup: 1x: 2023 +48.4047%, 2024 +4.3540%, 2025 -1.4064%; 2x: 2023 +47.1161%, 2024 -0.6772%, 2025 -1.7871%; 4x: 2023 +42.5923%, 2024 -3.4775%, 2025 -2.2570%. Negative months: 16/37 (1x), 15/37 (2x), 15/37 (4x).

## Decision: no promotion

C1 improves terminal training equity relative to B0 at all three cost levels, but deteriorates in 2025 and under severe costs. This is an **observed training result**, not proof of causal marginal sleeve contribution, robust long-run CAGR, or superiority to any external engine. **C1 fails the intended high-growth consistency objective and remains an unpromoted experimental architecture**. Do not rescue it by adjusting parameters, thresholds, sign or windows after seeing results.

## Remaining critical path

1. Independently attribute C1's four sleeves with controlled ablations and a frozen counterfactual protocol, rather than infer sleeve merit from total-equity comparison to B0.
2. Confirm exact invested-duration CAGR, PF/payoff/win rate/positive days, regime and tail concentration, and external venue execution assumptions with native documented fee/slippage evidence.
3. Preregister a genuinely distinct seven-slot architecture and complete chronological training/separate validation without opening any future holdout; only then consider freeze and external benchmarks.
4. Preserve XRP quarantine, contaminated Phase083 exclusion, V16/V99 Frozen and all paper state.
