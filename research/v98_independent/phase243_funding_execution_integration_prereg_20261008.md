# V98 Independent — Phase243 verified funding/execution integration gate (2026-10-08)

Status: PREREGISTERED / ACCOUNTING-ONLY / NO ALPHA / NO PROMOTION.
Branch: research/v98-independent-zero. Scope: V98-only training 2023-2025.

1. Audit all five native Phase206 funding CSVs before portfolio PnL: millisecond timestamp must equal UTC text; unique monotone 8h settlements, no missing slots, 0–50ms reporting jitter, finite rates and <2026 cutoff. Freeze each raw SHA256.
2. Map each event to its scheduled 8h boundary t (not its reporting jitter); charge position executed at open t to return interval [t,t+1). Both exact and jittered timestamps use the same convention, regardless of whether one is more profitable.
3. Enforce contiguous hourly open prices, five fixed V98 assets, causal signal_asof <= open(t)-1h, first/last in-fold weights flat, and no 2026+ observations. Reject any incomplete source or missing bar rather than filling zeros.
4. Run exact self-financing target-weight accounting with drift-induced rebalance fees and terminal liquidation under frozen 7/14/28 bp. Reconcile hourly equity, signed funding, price PnL, fees, turnover and source hashes.
5. Report MDD including starting wealth=1, hourly PF/payoff/win rate, compounded UTC daily positive days and tails, regime attribution without noncontiguous compounding, asset gross-path concentration and cancellation. Repeat deterministically.
6. The integration gate is a necessary accounting precondition, not evidence of positive alpha. Phase241/242/243 remain unpromoted until actual training, independent validation and untouched holdout protocols pass. No rejected families are rescued.

Known limitation: settlement mark-price variation inside each hourly bar cannot be inferred from hourly opens; stress-test this separately without choosing favorable conventions. The 2026+ holdout remains unopened.
