# V98 Independent Phase213 — post-mortem

Decision: **REJECT_FAMILY_NO_RESCUE**.

Evidence harvested from the preregistered deterministic Phase213 workflow on training folds only. Firewall `<2026-01-01` passed and two independent evaluator executions produced identical result-file SHA256 `56a9e154899d821bde814bec235f3defc807661cf9395da25ec1dfabc655f7e2`. Mechanical gate: 0/8 specs had base return > 0 and Profit Factor > 1 in all 2023/2024/2025 folds.

Failure mechanism is broad, not an isolated asset/regime accident. For frozen first spec `clv_L168_c60_hold3`, 2023 base return was -73.16%, PF 0.805, MDD -75.64%, win rate 29.19%, positive days 30.14%; every alt was negative. Bear, bull and sideways returns were all negative. Severe return was -92.22% and supersevere -99.35%. This is economically far below any promotion threshold and costs worsen it monotonically.

No sign inversion, regime rescue, asset deletion, threshold retuning, or opened-holdout selection is permitted. Phase213 family is closed. Validation/final holdout remain untouched. V16/V99 state is outside scope and unchanged.
