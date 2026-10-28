# V99 I1 — nonfixture numerical diagnostics firewall preregistration (2026-10-28 07:4x BRT)

## Scope and hypothesis (fixed before implementation)
The native event-to-661d bridge can compute provisional nonfixture wallet NAV but the only numeric screen `evaluate` deliberately rejects it. This is an **internal operational blocker** to inspecting full-source TRAIN economics after lawful input arrives; it must not be bypassed by relabeling synthetic fixtures as authenticated. Implement a separate `evaluate_provisional` API for **uncertified** nonfixture native event replay. Leave the existing official `evaluate` fixture-only and promotion gates unchanged.

### Fixed admissibility contract
- Input schema `V99_I1_FIXED_90W_DAILY_TRAIN_EQUITY_INPUT_V1`, `fixture is False`, `status == PROVISIONAL_UNCERTIFIED_NATIVE_EVENT_EQUITY`, all original-source/economic/fill/fee/paper/holdout/freeze/promotion flags exactly false, both severe/supersevere scenarios.
- Recompute the identical 661 daily clocks, five chronological folds, six 3x2 regimes, original-index passive benchmark, daily risk/tail concentration, drawdown, profit factor, severe/supersevere exposure-path divergence, numeric fold gates. Fail closed on forged flags, missing days, mismatched source paths, missing scenarios, invalid equity.
- Output is `PROVISIONAL_NONFIXTURE_NUMERIC_DIAGNOSTIC_NOT_CERTIFIED`, `source_fixture:false`, `numeric_train_pass_both_scenarios` is descriptive only; **all** certification, promotion, freeze, validation, holdout, order and paper flags remain false. No claim of historical profit even if numbers happen to be positive.
- The independent numeric oracle must recompute and check this provisional output, without importing the primary evaluator, while preserving the original fixture contract. Adversarial tests: forged source-certification flag, fake source fixture, wrong provenance status, altered numeric result and incomplete daily grid.
- CI must run the provisional diagnostic on clearly labeled synthetic event journals only, and verify the official `evaluate` still rejects the nonfixture output. This does not unlock historical economic TRAIN.

## Immutable safety and evidence
No modifications to Frozen V16/V99, legacy champion, paper/results, sealed validation 2023-10-01..2024-01-17, or final holdout >=2024-01-18. No orders or raw licensed files. Any CI SUCCESS only demonstrates software correctness. Current original full BTC/ETH 2021-12-09..2023-09-30 options BBO/size lifecycle archive, dated account-specific fees, inverse-coin margin/liquidation, settlement index and independent execution simulator evidence remain absent. **0/180 complete original option lifecycles certified; NO PROMOTION**.

## Decision
If adversarial tests and independent oracle pass, accept the *diagnostic capability only*. Otherwise revert or fix, never promote. Next actual critical step is a source-to-native-event builder bound to authenticated full quote bytes and the 180 original signal intents, then a genuine TRAIN run once source and native terms exist.
