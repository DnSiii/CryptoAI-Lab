# V98 Independent Phase1036 — P frozen source-only activation and concentration audit

**Scope:** inspect Phase1026 official source-only artifact `12493955010` from run `39934956461`. This report uses **no P historical PnL**, 2025 data, contaminated holdout or external engine benchmarks. It does not change frozen P code, target hashes, architecture, costs or leverage.

## Observed completed-hour source-only activation (18,288 hours, Dec-2022–Dec-2024)
- Growth Core: **826** hours with positive sleeve score.
- Opportunity: **913** hours.
- Relative Value: **12,915** hours.
- Stress/Recovery: **666** hours.
- P_full composed portfolio: **13,324** hours with positive target gross.
- P_core_only: **700** active hours; P_minus_relative_value: **1,242** active hours; P_minus_opportunity: **13,252**; P_minus_recovery: **13,018**.
- Router: risk-off **8,177** hours, neutral **4,494**, risk-on **5,617**.
- Each path reports **896** rebalance/update decisions; P_full source-target L1 turnover **339.10** (dimensionless sum of absolute target-weight changes), maximum single-asset target **0.70**, maximum gross target **1.65**.

## Structural finding and decision
Relative Value has the broadest activation by far (12,915 hours versus 826/913/666 for other sleeves). P_full active hours collapse from 13,324 to 1,242 when Relative Value is ablated, so the composed portfolio has **substantial temporal dependence** on that sleeve. These are source-only exposure statistics, not evidence of profitable or unprofitable contribution, and the sleeve activation hours overlap. The Phase1023 positive **marginal net log-wealth** tests remain mandatory for every ablation and each 2023/2024 fold, cost tier (base/severe), funding ordering and capital mode.

**Decision:** retain frozen P unchanged pending its preregistered 90-cell authenticated economics. Do not preemptively rescue or reweight it because of this source-only concentration. If P fails, reject and design a genuinely distinct complete architecture; if P passes, separately validate untouched 2025 before any external benchmark.
