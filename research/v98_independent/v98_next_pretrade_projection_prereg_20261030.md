# V98 Independent — next-architecture causal mixed-sleeve pretrade projection (2026-10-30)

**Infrastructure preregistration ONLY, NOT a candidate, NOT ND rescue.** ND is frozen rejected and cannot be rerun with this projection. The original ND physical run exposed an execution-level source-vs-carried-weight mismatch: each completed-close source target was <=.84, but next-open carried virtual sleeves plus refreshed sleeves could exceed .84. For **future, economically distinct** seven-slot candidates, define a deterministic pretrade projection before seeing their returns.

At open t, use ONLY previous virtual quantity q, current open price, known equity, previously completed-close target w and update flags, and scheduled funding-event boolean. Never use current funding rate, funding mark, current close/high/low, future return, validation, holdout or external benchmark.

1. Reconstruct raw virtual weights: updated sleeve uses its prior completed-close target, non-updated sleeve carries q * open / current equity.
2. Fixed virtual gross target cap .84; if scheduled funding event and preexisting virtual gross >.82, cap .82. If preexisting virtual gross >.84, cap .82. The source weights themselves must respect .84.
3. If core alone exceeds cap, scale core proportionally to cap; then proportionally scale all optional sleeves to remaining room. Do not rotate ranks, flip signs, reselect assets, change timing or modify raw alpha.
4. Pass projected weights into the one-way net atomic planner, which separately reserves 3% on event, validates intermediate leverage, costs, and post-funding <=.90. The projector is NOT a substitute for the physical ledger or independent validation.
5. Test adversarial mixed-update/price-drift/zero-optional/event cases with independently calculated gross and no future funding dependence. Fail closed on invalid shapes, NaNs, negative/zero equity/prices or unbounded source targets.

This contract is for next distinct architecture only. All existing rejected ND and prior original receipts remain unchanged. No PnL, no 2025+, no Frozen, no paper, no live.
