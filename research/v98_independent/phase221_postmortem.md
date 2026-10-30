# V98 Independent Phase221 — decision-grade postmortem

Status: **REJECT_FAMILY_NO_RESCUE**.

Evidence boundary: training folds only (2023/2024/2025); 2026+ remains unopened. Phase221 tested the preregistered BTC-beta residual cross-sectional continuation family with exactly eight frozen specs. The workflow rebuilt training-only data, passed namespace/firewall and static causality invariants, produced byte-identical result files on two independent deterministic executions (workflow SHA256 `917ceda9576886e131e3f8e1502e4a4d663e7e4b50c03fc7cb232896a6c5bfee`), verified monotone base -> severe -> supersevere return degradation, and found zero specs satisfying positive base return and PF>1 in every 2023/2024/2025 fold.

## Independent failure audit

A representative preregistered spec (`resbeta_W168_L24_hold4`) shows why this is not a near miss. In 2023 base it returned -11.73%, PF 0.9958, MDD -50.84%, win rate 47.18%, positive days 40.27%; severe fell to -65.61%, PF 0.9191, MDD -77.73%; supersevere to -94.79%, PF 0.7930, MDD -96.13%. Base regime decomposition is heterogeneous rather than robust: bear -11.96% / PF 0.9376, bull -16.20% / PF 0.9657, while sideways +19.65% / PF 1.0405. Asset contribution is also unstable: ETH -13.69%, XRP -3.82%, SOL -1.80%, BNB +0.97%. Maximum asset concentration reaches 67.53%. Median trade is negative (-4.62 bp) despite a positive right tail (p99 +2.62%), so occasional winners do not overcome the center of the distribution plus execution costs.

In 2024 the same spec is only marginally positive in base (+3.86%, PF 1.0100) but already has -31.77% MDD and depends materially on SOL (+23.16% asset return) while BNB/ETH/XRP are negative. Bear regime is -28.27% / PF 0.8984, versus bull +39.74% / PF 1.0721. Severe immediately destroys the small base edge (-60.95%, PF 0.9334, MDD -69.66%). This is regime/asset concentration plus insufficient gross edge, not a parameter-local defect.

Funding contributions are small relative to the observed PnL failure and do not rescue the family. The cost stress response is monotone and severe, consistent with turnover consuming a weak raw residual-continuation signal. No inversion, threshold tweak, window rescue, hold rescue, asset removal, or regime filter is permitted after seeing these outcomes.

## Decision

Reject the entire Phase221 frozen family. Do not promote any spec and do not use Phase221 outcomes to tune a neighboring residual-continuation variant. Current V98 champion remains unchanged. The next hypothesis must be scientifically distinct and preregistered before its result is observed.

## Provenance recovery

This namespaced copy reproduces the decision-grade evidence introduced by commit `eee06b7a7a9837eb1ad1af49a17c247613d9d382` at `reports/v98_independent_phase221_postmortem.md`; it restores V98 Independent namespace continuity without changing the decision or evidence boundary.