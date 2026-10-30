# V99 R106 — self-financing conservation oracle fail-closed hardening (2026-10-30, 10:5x BRT)

## Objective / scope
After the 09:47 original TRAIN finding that legacy weight-delta turnover is not sufficient for hourly quantity rebalancing, harden the **reusable** independent conservation verifier before any new complete engine can consume it. This is **not** a new alpha, C1/C2 retune, validation opening, funding certification, or claimed economic result. The previous 16,055-row original TRAIN results remain immutable diagnostics.

## Fixed checks before implementation
1. Reject nonfinite, negative, or >1% per-side modeled costs even when no turnover occurs. A zero cost is permitted for deterministic conservation tests, never as evidence of native fees.
2. Require exactly one-hour, strictly increasing, timezone-aware **UTC** journal timestamps; no skipped, duplicated, non-UTC or naive timestamps. Validate both production replay input and independent trace, including the final original hour.
3. In the independent oracle reject gross target weight >1.3, nonpositive/nonfinite pre-trade/post-fee/next-open NAV, and nonfinite fees/turnover. The oracle must remain algebraically independent of the production implicit-fee solver.
4. Add adversarial tests for invalid cost with zero trade, skipped hour, non-UTC time, overgross target, and negative final NAV. Preserve all previous tests.
5. Run the full **original canonical TRAIN-only** rejected C1/C2 audit in GitHub CI, including 16,055 hours per system/cost, two deterministic original replays and independent conservation. No sealed validation or holdout access. If original cache missing, fail closed. Confirm original published rejected ROI and no promotion unchanged.
6. Do not modify original C1/C2 strategy, V16/V99 Frozen, paper, champion, or historical reports. Any failure remains a software or source hold, not an invitation to alter rejected models.

## Outcome rule
Green CI is software/accounting integrity only. Historical costs are **modeled**; native historical fills, fee tier, funding settlement, margin and liquidation remain unverified. Status always **NO PROMOTION**. For I1, 658/661 days of original options two-sided executable quotes/size/arrival/marks/expiry plus license and dated native venue terms remain external missing evidence; do not fabricate or replace with trade prints.
