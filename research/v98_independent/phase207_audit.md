# V98 Independent — Phase207 audit

## Scope
Branch `research/v98-independent-zero`; V98 Independent only. Validation/final holdout remains unopened. No V16/V99 state is used.

## Execution integrity
- Training-only rebuild completed through 2025-12-31.
- Firewall passed for canonical prices and Phase206 funding snapshots: monotonic timestamps, no duplicates, no timestamp >= 2026-01-01.
- Two independent Phase207 evaluator invocations produced byte-identical result-file SHA256 `b4dba87d6031b0c5e4e0096c9acf837a43cd09c4d056f9f41f078635c1bbd162`.
- Workflow failed only at the final `git push` because the remote branch advanced concurrently; computation/reproduction themselves succeeded. The result is present on the branch and is therefore auditable.

## Failure-mechanism audit
The first preregistered cell (`res24h_beta30d_hold24h`) is decisively non-robust, not a near miss:
- 2023 base return -78.10%, PF 0.916, MDD -83.53%, positive days 40.82%; severe -85.41%; supersevere -93.54%.
- 2024 base return -11.74%, PF 1.003, MDD -41.35%; severe -40.79%; supersevere -77.94%.
- 2023 losses occur in bear, bull and sideways regimes, so a post-hoc regime rescue is forbidden and unsupported.
- 2023 base asset PnL is negative for every traded alt; the loss is therefore not attributable to one isolated symbol. Max loss-concentration metric is ~0.55, while the whole basket is losing.
- Tail median is already negative in 2023 base (-0.19% per trade), and transaction-cost stresses monotonically worsen the distribution.

This is evidence against the family mechanism rather than merely a cost problem: the unstressed/base signal already lacks stable edge and severe/supersevere costs amplify, rather than create, the failure.

## Decision discipline
Do not invert Phase207, cherry-pick assets/regimes, or tune beta/residual/holding windows from opened results. No promotion is justified from the audited evidence. Champion remains unchanged. The next hypothesis must be scientifically distinct and preregistered before its results are observed.
