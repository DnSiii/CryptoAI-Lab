# V98 Independent Phase1254 — AI exact-source reproducibility REJECTION (2026-10-23)

Official independent 3x2 runner gate: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40017405255. **FAIL**, despite all six source-generation jobs completing and numerical diagnostic passing. The frozen preregistered gate demanded exact raw hashes across all six independent Ubuntu 22.04/24.04 runs.

Five of six runner instances matched the baseline exactly. Ubuntu 24.04 replica 2 differed in:
- Benign Growth: 2 of 3,600 source weights, maximum 1.000005634e-12; both rounded-to-10 and rounded-to-9 diagnostic hashes matched.
- Benign RV beta: 1,976 values, maximum 8.860967516e-15; rounded-to-9 diagnostic hashes matched.
- Crisis Relative Value: 19 source weights, maximum 1.000000027e-9; rounded-to-8 diagnostic hash **still did not match**, rounded-to-7 did. No sign differences above 1e-8, but **exact SHA256 failed**.
- Crisis RV beta: 1,971 values, maximum 8.860967516e-15; rounded-to-9 diagnostic hashes matched.

The earlier 2-runner Phase1253 exact match (40017202521) was insufficient to detect this intermittent variation. The earlier first full 180-cell run (40016172237) independently passed 180/180 but failed crossrunner turnover reconciliation at cell 114 by USD 0.000022154 versus allowed USD 0.000010; therefore it remains ineligible. The post-9-decimal RV revision still did not pass Phase1254 strict six-runner source reproducibility.

**Final decision for this frozen AI candidate:** **REJECT_AI_FULL_REPRODUCIBILITY**. Do not freeze, benchmark, run historical system PnL, or alter AI source rounding/thresholds/signs/windows/fees/gross/governor/allocator to cosmetically rescue it. Keep all original receipts and failed gates. AI's synthetic 180/180 per-run survival is not economic evidence and does not override exact-source failure.

**Next architecture:** preregister a genuinely distinct AJ complete seven-slot engine using deterministic non-SVD rank-based relative-value weights and different growth/opportunity/stress/router/allocator/risk hypotheses. Reuse only generic independently tested V98 accounting primitives, not rejected AI strategy signals/parameters. No 2025 validation, 2026+, XRP, Phase083 or external benchmarks. V16/V99 untouched.
