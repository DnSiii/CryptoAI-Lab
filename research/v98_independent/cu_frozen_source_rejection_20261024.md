# V98 Independent CU — frozen source-only rejection (2026-10-24)

**Decision: REJECT_CU_SOURCE_INACTIVITY.** Preregistered source activity gate failed before any system PnL. CU is permanently rejected; no after-result sign, threshold, window, budget or module rescue.

- Preregistration commit `5beec41709523e4c09716096fef130679c7cef10` predates CU source execution.
- Official authenticated pinned Clean-4 2022-2024 source run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40147893458 ; source artifact https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40147893458/artifacts/12581174627 .
- Causal source static test **passed**. 2023 effective nonzero epochs: Growth 18 (minimum 4), Opportunity 24 (minimum 4), Relative Value 28 (minimum 8), **Stress/Recovery 1 (minimum 4; FAIL)**. 2024: Growth 18, Opportunity 26, Relative Value 31, Stress/Recovery 5 (all pass).
- The source gate rejected CU **before native settlement, historical PnL, or 20-cell execution**. No CAGR, drawdown or profitability claims are authorized for CU.
- Log labels `REJECU_CU_SOURCE_INACUIVITY` and `distincu_active_signal_transitions` are cosmetic identifier typos from automatic CT->CU text replacement. They do not alter the numeric gate, which returned exit code 2, or justify a rerun or rescue.
- 2025 holdout not opened; 2026+ not accessed; XRP quarantined. No V16/V99 Frozen, V99 research/workflows/reports or paper state touched. No external benchmark or live order.

**Next critical-path hypothesis must be genuinely distinct and precommitted**, with a stress/recovery mechanism that is active in both training years; do not borrow any CU signal or tuned parameter.
