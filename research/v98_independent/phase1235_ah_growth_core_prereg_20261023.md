# V98 Independent Phase1235 — AH signed funding-adjusted growth core prereg (2026-10-23)

First source-only implementation of distinct AH Phase1233, **not** an AG/AD/AE rescue. Clean-4 only; no historical AH PnL, 2025 validation, 2026+, XRP, Phase083 or external benchmarks.

At completed hourly close t (never before t+1 open):
- Use 120h sum of each asset's log return minus equal-weight Clean-4 log return, subtract actual *signed native 8h funding rate* accrued over those 120h for a hypothetical long unit. No inferred funding between native events.
- Confirm the **sign** using the last 24h excess return; otherwise directional idiosyncratic score is zero. Scale by the median absolute 120h residual magnitude with a fixed 1e-4 floor; clip score to [-3,+3] for numerical stability, not as a return objective ceiling.
- Separately compute the 48h equal-weight market log drift: if >+0.005 add +0.15 to each asset; if <-0.005 add -0.15 to each asset; otherwise no aggregate beta. This is a distinct market component, not AG long-only source.
- Normalize the final signed vector by gross absolute sum (if nonzero), without assigning any actual leverage or trade. Downstream AH allocator/governor will determine collateralized size and cash.

Precommitted tests: shape, both long and short activity, native funding sign sensitivity, no future perturbation, strict t-1 execution, deterministic two-OS source hash. Any source-test failure is recorded and cannot be hidden as positive economic evidence. The complete AH seven-slot 180-cell gate remains controlling.
